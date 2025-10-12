from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from app.models.schemas import (
    Text2SQLRequest, 
    Text2SQLResponse, 
    ChatText2SQLRequest,
    AgenticText2SQLRequest
)
from app.services.simple_text2sql import SimpleText2SQLService
from app.services.advanced_text2sql import AdvancedText2SQLService
from app.services.chat_text2sql import ChatText2SQLService
from app.services.agentic_text2sql import AgenticText2SQLService

router = APIRouter()

# Service instances
simple_service = SimpleText2SQLService()
advanced_service = AdvancedText2SQLService()
chat_service = ChatText2SQLService()
agentic_service = AgenticText2SQLService()

@router.post("/simple", response_model=Text2SQLResponse)
async def simple_text2sql(request: Text2SQLRequest):
    """
    Convert natural language to SQL using simple schema-based approach
    """
    try:
        # Generate SQL
        sql_result = simple_service.generate_sql(request.query)

        # Execute if requested
        execution_result = None
        parsed_response = None
        if request.execute:
            execution_result = simple_service.execute_query(sql_result["sql"])

            # Generate natural language response using parser LLM
            parsed_response = simple_service.parse_results_to_text(
                user_query=request.query,
                sql_query=sql_result["sql"],
                execution_result=execution_result
            )

        return Text2SQLResponse(
            sql=sql_result["sql"],
            method=sql_result["method"],
            execution_result=execution_result,
            parsed_response=parsed_response
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/advanced", response_model=Text2SQLResponse)
async def advanced_text2sql(request: Text2SQLRequest):
    """
    Convert natural language to SQL using advanced approach with BM25 retrieval
    """
    try:
        # Generate SQL
        sql_result = advanced_service.generate_sql(request.query)

        # Execute if requested
        execution_result = None
        parsed_response = None
        if request.execute:
            execution_result = advanced_service.execute_query(sql_result["sql"])

            # Generate natural language response using parser LLM
            parsed_response = advanced_service.parse_results_to_text(
                user_query=request.query,
                sql_query=sql_result["sql"],
                execution_result=execution_result
            )

        return Text2SQLResponse(
            sql=sql_result["sql"],
            method=sql_result["method"],
            context_used=sql_result.get("context_used"),
            execution_result=execution_result,
            parsed_response=parsed_response
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=Text2SQLResponse)
async def chat_text2sql(request: ChatText2SQLRequest):
    """
    Convert natural language to SQL with conversation context
    """
    try:
        # Generate SQL with chat context
        sql_result = chat_service.generate_sql_with_context(
            request.query,
            request.session_id
        )

        # Execute if requested
        execution_result = None
        if request.execute:
            execution_result = chat_service.execute_query(sql_result["sql"])

        return Text2SQLResponse(
            sql=sql_result["sql"],
            method=sql_result["method"],
            session_id=sql_result.get("session_id"),
            resolved_query=sql_result.get("resolved_query"),
            context_used=sql_result.get("context_used"),
            execution_result=execution_result
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/agentic", response_model=Text2SQLResponse)
async def agentic_text2sql(request: AgenticText2SQLRequest):
    """
    Convert natural language to SQL using agentic approach with tools
    """
    try:
        # Generate SQL using agent
        sql_result = agentic_service.generate_sql_with_agent(
            user_query=request.query,
            session_id=request.session_id,
            max_iterations=request.max_iterations
        )

        # Handle clarification requests
        if sql_result.get("needs_clarification"):
            raise HTTPException(
                status_code=400,
                detail={
                    "needs_clarification": True,
                    "questions": sql_result.get("questions", [])
                }
            )

        if not sql_result.get("success"):
            raise HTTPException(status_code=500, detail=sql_result.get("error", "Unknown error"))

        # Get execution result and parsed response from workflow
        execution_result = sql_result.get("execution_result")
        parsed_response = sql_result.get("parsed_response")

        # Execute if requested but not already executed by agent
        if request.execute and not execution_result:
            execution_result = agentic_service.execute_query(sql_result["sql"])

            # Parse results if execution succeeded but not already parsed
            if execution_result and execution_result.get("success") and not parsed_response:
                try:
                    parsed_response = agentic_service.parse_results_to_text(
                        user_query=request.query,
                        sql_query=sql_result["sql"],
                        execution_result=execution_result
                    )
                except Exception as e:
                    print(f"Warning: Failed to parse results to text: {str(e)}")
                    parsed_response = None

        return Text2SQLResponse(
            sql=sql_result["sql"],
            method=sql_result["method"],
            session_id=sql_result.get("session_id"),
            resolved_query=sql_result.get("resolved_query"),
            iterations=sql_result.get("iterations"),
            tool_calls=sql_result.get("tool_calls"),
            execution_result=execution_result,
            validation_result=sql_result.get("validation_result"),
            agentic_context=sql_result.get("context_used"),
            parsed_response=parsed_response
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chat/{session_id}")
async def clear_chat_history(session_id: str):
    """
    Clear chat history for a specific session
    """
    try:
        chat_service.clear_history(session_id)
        return {"message": f"Chat history cleared for session {session_id}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools")
async def list_available_tools():
    """
    List all available tools for the agentic approach
    """
    tools = []
    for tool_name, tool in agentic_service.tools.items():
        tools.append({
            "name": tool.name,
            "description": tool.description
        })
    
    return {"tools": tools}

@router.post("/execute")
async def execute_sql(request: Dict[str, Any]):
    """
    Execute a raw SQL query directly
    """
    try:
        sql = request.get("sql")
        if not sql:
            raise HTTPException(status_code=400, detail="SQL query is required")
        
        result = simple_service.execute_query(sql)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))