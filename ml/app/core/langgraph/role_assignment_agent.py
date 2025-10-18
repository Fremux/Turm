"""Role assignment agent for determining who should handle the request."""

import json
from typing import Optional, Dict, Any, List
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.logging import logger
from app.schemas.classification import RoleAssignment


class RoleAssignmentAgent:
    """Agent for assigning requests to appropriate roles based on organizational structure."""

    def __init__(self):
        """Initialize the role assignment agent."""
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.1,
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL if settings.LLM_BASE_URL else None,
            streaming=False,
        )
        
        # Load organizational structure
        self.org_data = self._load_org_data()
        self.task_coverage = self.org_data.get("task_coverage", {})
        
        # Build node lookup for fast access
        self.node_lookup = {}
        self._build_node_lookup(self.org_data)
        
        # Cache for role assignments
        self._cache = {}
        
        self.system_prompt = self._build_system_prompt()

    def _load_org_data(self) -> Dict[str, Any]:
        """Load organizational data from users.json."""
        try:
            org_file = Path("/root/Turm/ml/users.json")
            with open(org_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error("failed_to_load_org_data", error=str(e))
            return {}

    def _build_node_lookup(self, node: Dict[str, Any], path: List[str] = None):
        """Recursively build lookup table for all nodes."""
        if path is None:
            path = []
        
        node_id = node.get("id")
        if node_id:
            self.node_lookup[node_id] = {
                "id": node_id,
                "title": node.get("title", ""),
                "position": node.get("position"),
                "unit_type": node.get("unit_type", ""),
                "path": path + [node.get("title", "")]
            }
        
        for child in node.get("children", []):
            self._build_node_lookup(child, path + [node.get("title", "")])

    def _build_system_prompt(self) -> str:
        """Build system prompt with organizational data."""
        
        # Format task coverage in a readable way
        coverage_text = json.dumps(self.task_coverage, ensure_ascii=False, indent=2)
        
        return f"""Ты эксперт по маршрутизации запросов в организационной структуре компании.

ВАЖНО: Отвечай ТОЛЬКО на русском языке.

## Организационные данные:

{coverage_text}

## Правила интерпретации запроса:

1) НОРМАЛИЗАЦИЯ:
   - Приведи запрос к нижнему регистру, убери пунктуацию, замени типичные синонимы.
   - Разбей ключи из actions/entities/systems по разделителям «/» и пробуй матчить по леммам/подстрокам.

2) ПОИСК СОВПАДЕНИЙ:
   - Сначала ищи точное или частичное совпадение в actions указанного домена (HR/IT/Finance/Office).
   - Затем в entities/systems/systems_examples.
   - Если совпадений несколько — выбери самый специфичный ключ (более длинный и точно соответствующий смыслу).
   - Разрешается мягкий фуззи-матч (по подстрокам) с высоким порогом релевантности.

3) РОЛИ:
   - Основной исполнитель: узел по handled_by_id (ОБЯЗАТЕЛЬНО).
   - Эскалация: узел по escalate_to_id (если присутствует).
   - Координация: узел по coord_with_id (если присутствует).

4) ГРАНИЧНЫЕ СЛУЧАИ:
   - Если подходящих ролей несколько — верни их все в alternatives, отсортируй по релевантности.
   - Если ничего не найдено — верни пустой результат с объяснением.
   - Никаких домыслов: отвечай только теми ролями, что присутствуют в данных.

5) ФОРМАТ ОТВЕТА:
   Верни ТОЛЬКО JSON в формате:

   {{
     "domain": "<HR|IT|Finance|Office>",
     "matched_key": "<ключ из actions/entities/systems>",
     "primary_role_id": "<handled_by_id>",
     "escalation_role_id": "<escalate_to_id или null>",
     "coordination_role_id": "<coord_with_id или null>",
     "alternatives": [
       {{"domain": "...", "matched_key": "...", "primary_role_id": "..."}}
     ],
     "confidence": 0.85,
     "reason": "Короткое объяснение выбора"
   }}

ПРИМЕРЫ:

Запрос: "Нужно оформить отпуск", domain: "HR"
→ {{"domain": "HR", "matched_key": "график/дистант/0.5 ставки/отпуск/командировка", "primary_role_id": "rosatom-hr-specialist", "escalation_role_id": null, "coordination_role_id": null, "alternatives": [], "confidence": 0.95, "reason": "Запрос содержит слово 'отпуск', которое точно соответствует ключу в entities"}}

Запрос: "Открыть доступ к VPN", domain: "IT"
→ {{"domain": "IT", "matched_key": "создать/изменить/восстановить доступ (AD/VPN/SSO/MFA)", "primary_role_id": "rosatom-it-l1", "escalation_role_id": "rosatom-it-sys", "coordination_role_id": null, "alternatives": [], "confidence": 0.95, "reason": "Запрос о доступе к VPN, что покрывается ключом в actions"}}

Запрос: "Починить Wi-Fi", domain: "IT"
→ {{"domain": "IT", "matched_key": "починить сеть/VPN/Wi‑Fi/почту", "primary_role_id": "rosatom-it-net", "escalation_role_id": "rosatom-it-lb", "coordination_role_id": null, "alternatives": [], "confidence": 0.95, "reason": "Wi-Fi упоминается в ключе actions"}}

Запрос: "Записать на обучение", domain: "HR"
→ {{"domain": "HR", "matched_key": "записать на обучение", "primary_role_id": "rosatom-hr-lms", "escalation_role_id": null, "coordination_role_id": null, "alternatives": [], "confidence": 0.95, "reason": "Точное совпадение с ключом в actions"}}

Запрос: "Оформить пропуск", domain: "Office"
→ {{"domain": "Office", "matched_key": "пропуск (оформить/выдать/заменить/продлить)", "primary_role_id": "rosatom-pass-operator", "escalation_role_id": null, "coordination_role_id": null, "alternatives": [], "confidence": 0.95, "reason": "Слово 'оформить пропуск' соответствует ключу в actions"}}

Если ничего не найдено, верни:
{{"domain": null, "matched_key": null, "primary_role_id": null, "escalation_role_id": null, "coordination_role_id": null, "alternatives": [], "confidence": 0.0, "reason": "Не найдено подходящих ключей в task_coverage"}}
"""

    async def assign_role(
        self, 
        message: str, 
        domain: Optional[str] = None,
        intent: Optional[str] = None
    ) -> Optional[RoleAssignment]:
        """Assign appropriate role for handling the request.
        
        Args:
            message: The user message
            domain: The department domain (HR/IT/Finance/Office)
            intent: The user intent type
            
        Returns:
            RoleAssignment object or None if assignment fails
        """
        try:
            # Only assign roles for access_request or information_request
            if intent not in ["access_request", "information_request"]:
                logger.info("role_assignment_skipped", intent=intent, reason="Not applicable for this intent")
                return None
            
            # Need domain to assign role
            if not domain or domain == "other":
                logger.info("role_assignment_skipped", domain=domain, reason="Domain is other or unknown")
                return None
            
            # Trim message
            message_trimmed = message[:500] if len(message) > 500 else message
            
            # Check cache
            cache_key = f"{domain}:{message_trimmed.lower().strip()}"
            if cache_key in self._cache:
                logger.info("role_assignment_cache_hit")
                return self._cache[cache_key]
            
            # Prepare prompt
            user_prompt = f"Запрос: \"{message_trimmed}\"\nДомен: {domain}"
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages, max_tokens=800)
            
            # Parse JSON response
            content = response.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            # Parse JSON
            data = json.loads(content)
            
            # If no role found, return None
            if not data.get("primary_role_id"):
                logger.info("role_assignment_not_found", message=message_trimmed, domain=domain)
                return None
            
            # Resolve role details from node lookup
            primary_role = self._get_role_details(data.get("primary_role_id"))
            escalation_role = self._get_role_details(data.get("escalation_role_id")) if data.get("escalation_role_id") else None
            coordination_role = self._get_role_details(data.get("coordination_role_id")) if data.get("coordination_role_id") else None
            
            # Process alternatives
            alternatives = []
            for alt in data.get("alternatives", [])[:3]:  # Limit to 3 alternatives
                alt_primary = self._get_role_details(alt.get("primary_role_id"))
                if alt_primary:
                    alternatives.append({
                        "domain": alt.get("domain"),
                        "matched_key": alt.get("matched_key"),
                        "primary_role": alt_primary
                    })
            
            # Create RoleAssignment object
            assignment = RoleAssignment(
                domain=data.get("domain"),
                matched_key=data.get("matched_key"),
                primary_role=primary_role,
                escalation_role=escalation_role,
                coordination_role=coordination_role,
                alternatives=alternatives if alternatives else None,
                confidence=data.get("confidence", 0.8),
                reason=data.get("reason", "")
            )
            
            # Cache the result
            if len(self._cache) > 100:
                self._cache.pop(next(iter(self._cache)))
            self._cache[cache_key] = assignment
            
            logger.info(
                "role_assigned",
                domain=assignment.domain,
                matched_key=assignment.matched_key,
                primary_role_id=assignment.primary_role.id if assignment.primary_role else None,
                confidence=assignment.confidence
            )
            
            return assignment
            
        except json.JSONDecodeError as e:
            logger.error("role_assignment_json_parse_error", error=str(e), response=content)
            return None
        except Exception as e:
            logger.error("role_assignment_error", error=str(e), exc_info=True)
            return None

    def _get_role_details(self, role_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Get role details from node lookup."""
        if not role_id:
            return None
        
        node = self.node_lookup.get(role_id)
        if not node:
            logger.warning("role_not_found_in_lookup", role_id=role_id)
            return None
        
        return {
            "id": node["id"],
            "title": node["title"],
            "position": node["position"],
            "path": node["path"]
        }


# Global instance
role_assignment_agent = RoleAssignmentAgent()

