"""Service for automatically assigning tasks to organization roles based on capabilities."""

from typing import Optional, List, Dict, Any
from sqlmodel import Session, select, or_, and_
from difflib import SequenceMatcher

from app.core.logging import logger
from app.models.organization import OrganizationUnit, TaskCapabilityMapping


class RoleAssignmentService:
    """Service for finding the best role to assign a task to."""
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text by replacing synonyms with canonical forms."""
        text = text.lower()
        
        # Action verb synonyms
        synonyms = {
            'починить': 'настроить',
            'отремонтировать': 'настроить',
            'исправить': 'настроить',
            'оформить': 'создать',
            'сделать': 'создать',
            'предоставить': 'выдать',
            'дать': 'выдать',
        }
        
        for original, replacement in synonyms.items():
            text = text.replace(original, replacement)
        
        return text
    
    def find_best_role(
        self,
        task_summary: str,
        task_description: str,
        category: Optional[str],
        session: Session
    ) -> Optional[OrganizationUnit]:
        """Find the best role to assign a task to based on task details.
        
        Args:
            task_summary: Brief task summary
            task_description: Detailed task description
            category: Task category (hr, it, finance, office)
            session: Database session
            
        Returns:
            OrganizationUnit if a match is found, None otherwise
        """
        try:
            # Combine and normalize text for keyword matching
            task_text = f"{task_summary} {task_description}".lower()
            task_text = self._normalize_text(task_text)
            
            # Get all capability mappings for this category
            query = select(TaskCapabilityMapping)
            if category:
                query = query.where(TaskCapabilityMapping.category == category.lower())
            
            mappings = session.exec(query).all()
            
            if not mappings:
                logger.debug(f"No capability mappings found for category: {category}")
                return None
            
            # Score each mapping based on keyword matches
            scored_mappings = []
            for mapping in mappings:
                score = self._calculate_match_score(
                    task_text,
                    mapping.keywords,
                    mapping.action_type
                )
                
                if score > 0:
                    scored_mappings.append((mapping, score))
            
            if not scored_mappings:
                logger.debug(f"No matching roles found for task: {task_summary[:50]}...")
                return None
            
            # Sort by score (descending) and priority (descending)
            scored_mappings.sort(key=lambda x: (x[1], x[0].priority), reverse=True)
            
            # Get the best match
            best_mapping, best_score = scored_mappings[0]
            
            # Load the organization unit
            role = session.get(OrganizationUnit, best_mapping.handled_by_unit_id)
            
            if role:
                logger.info(
                    "role_assigned",
                    task_summary=task_summary[:100],
                    role_id=role.external_id,
                    role_title=role.title,
                    match_score=best_score,
                    match_action=best_mapping.action_type
                )
            
            return role
            
        except Exception as e:
            logger.error(f"Error finding best role: {e}", exc_info=True)
            return None
    
    def _calculate_match_score(
        self,
        task_text: str,
        keywords: List[str],
        action_type: str
    ) -> float:
        """Calculate how well a task matches a set of keywords.
        
        Args:
            task_text: Task text to match against
            keywords: List of keywords from capability mapping
            action_type: Full action type description
            
        Returns:
            Match score (0.0 - 1.0)
        """
        score = 0.0
        keyword_count = len(keywords)
        
        if keyword_count == 0:
            return 0.0
        
        # Exact keyword matches (high priority - 70%)
        exact_matches = 0
        total_keyword_weight = 0
        
        # Action verbs that indicate hands-on work (not just documentation)
        action_verbs = ['создать', 'настроить', 'починить', 'восстановить', 'изменить', 
                       'установить', 'устранить', 'выдать права', 'добавить', 'удалить']
        
        for keyword in keywords:
            keyword_weight = 1.0
            
            # Boost weight for action verbs
            if any(verb in keyword for verb in action_verbs):
                keyword_weight = 1.5
            
            # Boost for specific technical terms (VPN, AD, etc)
            if keyword in ['vpn', 'ad', 'доступ', 'учетка', 'права']:
                keyword_weight = 2.0
            
            if keyword in task_text:
                exact_matches += keyword_weight
            
            total_keyword_weight += keyword_weight
        
        # Calculate weighted exact match score
        if total_keyword_weight > 0:
            score += (exact_matches / total_keyword_weight) * 0.7
        
        # Fuzzy matching only for very close matches (reduced weight - 20%)
        action_lower = action_type.lower()
        # Only consider first 100 chars to avoid bias from long descriptions
        action_short = action_lower[:100]
        similarity = SequenceMatcher(None, task_text[:100], action_short).ratio()
        
        # Only add fuzzy score if similarity is high enough
        if similarity > 0.3:
            score += similarity * 0.2
        
        # Bonus for multiple keyword matches (10%)
        if exact_matches > 1:
            score += 0.1
        
        # Penalty for too generic mappings (like "инструкции")
        generic_terms = ['инструкции', 'шаблоны', 'регламенты', 'kb']
        if any(term in action_lower for term in generic_terms):
            # Only penalize if task has specific action words
            if any(verb in task_text for verb in action_verbs):
                score *= 0.5  # Reduce score by half
        
        return min(score, 1.0)
    
    def get_role_by_id(
        self,
        role_id: int,
        session: Session
    ) -> Optional[OrganizationUnit]:
        """Get a role by its ID."""
        return session.get(OrganizationUnit, role_id)
    
    def get_role_by_external_id(
        self,
        external_id: str,
        session: Session
    ) -> Optional[OrganizationUnit]:
        """Get a role by its external ID (from users.json)."""
        return session.exec(
            select(OrganizationUnit).where(OrganizationUnit.external_id == external_id)
        ).first()
    
    def get_all_roles(
        self,
        session: Session,
        unit_type: Optional[str] = None,
        is_active: bool = True
    ) -> List[OrganizationUnit]:
        """Get all roles, optionally filtered by type."""
        query = select(OrganizationUnit).where(OrganizationUnit.is_active == is_active)
        
        if unit_type:
            query = query.where(OrganizationUnit.unit_type == unit_type)
        
        return list(session.exec(query).all())


# Global instance
role_assignment_service = RoleAssignmentService()

