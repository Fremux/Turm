"""Knowledge base search tool for ReAct agent.

This tool enables the agent to search for relevant information in Qdrant
vector database based on the problem category (IT, HR, Finance, Office).
"""

from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from app.services.qdrant_service import qdrant_service
from app.core.logging import logger


class KnowledgeSearchInput(BaseModel):
    """Input schema for knowledge base search."""
    
    query: str = Field(
        ...,
        description="Поисковый запрос для поиска в базе знаний. Должен быть конкретным и содержать ключевые слова проблемы."
    )
    category: str = Field(
        ...,
        description="Категория для поиска: 'it', 'hr', 'finance' или 'office'. Определяет в какой коллекции искать."
    )
    limit: int = Field(
        default=5,
        description="Максимальное количество результатов (по умолчанию 5)"
    )


class KnowledgeSearchTool(BaseTool):
    """Tool for searching relevant information in the knowledge base."""
    
    name: str = "search_knowledge_base"
    description: str = """
    Ищет релевантную информацию в базе знаний компании по категории проблемы.
    
    Используй этот инструмент когда:
    - Нужно найти документацию, инструкции или решения похожих проблем
    - Проблема относится к внутренним системам или процессам компании
    - Нужна специфичная информация по IT, HR, Finance или Office процедурам
    
    Входные параметры:
    - query: конкретный поисковый запрос с ключевыми словами
    - category: категория ('it', 'hr', 'finance', 'office')
    - limit: количество результатов (по умолчанию 5)
    
    Возвращает список релевантных документов с оценкой похожести (score).
    Чем выше score (ближе к 1.0), тем более релевантен документ.
    """
    args_schema: Type[BaseModel] = KnowledgeSearchInput
    
    async def _arun(
        self,
        query: str,
        category: str,
        limit: int = 5
    ) -> str:
        """Search the knowledge base asynchronously.
        
        Args:
            query: Search query
            category: Category to search in (it/hr/finance/office)
            limit: Maximum number of results
            
        Returns:
            Formatted search results as string
        """
        try:
            # Map category to collection name
            category_lower = category.lower()
            collection_map = {
                "it": "it",
                "hr": "hr",
                "finance": "finance",
                "office": "office"
            }
            
            collection_name = collection_map.get(category_lower)
            if not collection_name:
                return f"Ошибка: неизвестная категория '{category}'. Доступные: it, hr, finance, office"
            
            # Get category embedding settings from database
            from sqlmodel import Session, select
            from app.models.category import Category
            from app.services.database import database_service
            from app.core.embedding_models import get_model_info, DEFAULT_MODEL_NAME, DEFAULT_DIMENSION
            
            embedding_model = DEFAULT_MODEL_NAME
            embedding_dim = DEFAULT_DIMENSION
            
            with Session(database_service.engine) as db:
                cat = db.exec(select(Category).where(Category.name == category_lower)).first()
                if cat and cat.embedding_model:
                    # Get model info - use actual dimension from model mapping
                    model_name, model_dim = get_model_info(cat.embedding_model)
                    embedding_model = model_name
                    embedding_dim = cat.embedding_dimension or model_dim
                    
                    # Validate dimension matches model
                    if cat.embedding_dimension and cat.embedding_dimension != model_dim:
                        logger.warning(
                            "dimension_mismatch",
                            category=category,
                            db_dimension=cat.embedding_dimension,
                            model_dimension=model_dim,
                            model=cat.embedding_model,
                            using_dimension=cat.embedding_dimension
                        )
                        # Use what's in DB (as collection was created with it)
                        embedding_dim = cat.embedding_dimension
            
            logger.info(
                "knowledge_search_started",
                query=query,
                category=category,
                collection=collection_name,
                limit=limit,
                embedding_model=embedding_model,
                embedding_dim=embedding_dim
            )
            
            # Search in Qdrant with category-specific embeddings
            results = await qdrant_service.search(
                query=query,
                limit=limit,
                collection_name=collection_name,
                embedding_model=embedding_model,
                embedding_dimension=embedding_dim
            )
            
            if not results:
                logger.info("knowledge_search_no_results", query=query, category=category)
                return f"По запросу '{query}' в категории {category} ничего не найдено в базе знаний."
            
            # Format results
            formatted_output = f"Найдено {len(results)} документов в базе знаний (категория: {category}):\n\n"
            
            for idx, result in enumerate(results, 1):
                score = result.get("score", 0.0)
                text = result.get("text", "")
                file_path = result.get("file_path", "неизвестный источник")
                
                # Format each result
                formatted_output += f"--- Документ {idx} (релевантность: {score:.2f}) ---\n"
                formatted_output += f"Источник: {file_path}\n"
                formatted_output += f"Содержание:\n{text}\n\n"
            
            logger.info(
                "knowledge_search_completed",
                query=query,
                category=category,
                results_count=len(results),
                avg_score=sum(r.get("score", 0) for r in results) / len(results) if results else 0
            )
            
            return formatted_output
            
        except Exception as e:
            error_msg = f"Ошибка при поиске в базе знаний: {str(e)}"
            logger.error("knowledge_search_error", error=str(e), query=query, category=category, exc_info=True)
            return error_msg
    
    def _run(
        self,
        query: str,
        category: str,
        limit: int = 5
    ) -> str:
        """Synchronous version (not implemented - use async)."""
        raise NotImplementedError("Use async version (_arun) instead")

