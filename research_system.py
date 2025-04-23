import os
import logging
from typing import TypedDict, List, Dict, Any
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

# Load environment variables
load_dotenv()

# Initialize LLMs and tools
research_llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.7)
drafting_llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.4)
tavily_tool = TavilySearchResults(max_results=5)

# Define state schema
class AgentState(TypedDict):
    query: str
    research_data: List[Dict[str, Any]]
    definition: str
    suggestions: List[Dict[str, str]]
    related_questions: List[str]

# Research agent
def research_agent(state: AgentState) -> Dict[str, Any]:
    logger = logging.getLogger(__name__)
    logger.info("Research agent started for query: %s", state["query"])
    try:
        results = tavily_tool.invoke({"query": state["query"]})
        logger.info("Collected %d research items", len(results))
        logger.debug("Research data sample: %s", results[0]['content'][:100] if results else "No results")
        return {"research_data": results}
    except Exception as e:
        logger.error("Research failed: %s", str(e), exc_info=True)
        raise

# Definition extraction agent
def definition_agent(state: AgentState) -> Dict[str, Any]:
    logger = logging.getLogger(__name__)
    logger.info("Definition agent started for query: %s", state["query"])
    try:
        prompt = f"""
        Please provide a clear, concise definition of "{state['query']}".
        Keep it under 3 sentences and make it accessible to a general audience.
        Focus only on defining what it is in straightforward terms.
        """
        response = research_llm.invoke([HumanMessage(content=prompt)])
        logger.info("Definition extraction completed")
        logger.debug("Definition: %s", response.content[:100])
        return {"definition": response.content}
    except Exception as e:
        logger.error("Definition extraction failed: %s", str(e), exc_info=True)
        raise

# Suggestions generation agent
def suggestions_agent(state: AgentState) -> Dict[str, Any]:
    logger = logging.getLogger(__name__)
    logger.info("Suggestions agent started with %d research items", len(state["research_data"]))
    try:
        research_context = "\n".join(
            [f"• {res['content'][:200]}..." for res in state["research_data"]]
        )
        prompt = f"""
        Based on the following research about "{state['query']}":
        
        {research_context}
        
        Generate 4 resource suggestions that would be helpful for someone wanting to learn more about "{state['query']}".
        
        Format each suggestion as a JSON object with "title" and "description" fields.
        For example:
        [
            {{"title": "Introduction Guide", "description": "A beginner's overview of the topic"}},
            ...
        ]
        
        Make the suggestions diverse and covering different aspects or difficulty levels.
        """
        response = research_llm.invoke([HumanMessage(content=prompt)])
        logger.info("Suggestions generation completed")
        
        # Process the response to extract JSON
        content = response.content
        import re
        import json
        
        json_match = re.search(r'\[(.*?)\]', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                suggestions = json.loads(json_str)
            except:
                suggestions = [
                    {"title": f"Resource on {state['query']}", "description": "An overview of the topic"},
                    {"title": f"Advanced {state['query']}", "description": "Deeper insights into the subject"},
                    {"title": f"{state['query']} in Practice", "description": "Real-world applications"},
                    {"title": f"Learning {state['query']}", "description": "Educational resources"}
                ]
        else:
            suggestions = [
                {"title": f"Resource on {state['query']}", "description": "An overview of the topic"},
                {"title": f"Advanced {state['query']}", "description": "Deeper insights into the subject"},
                {"title": f"{state['query']} in Practice", "description": "Real-world applications"},
                {"title": f"Learning {state['query']}", "description": "Educational resources"}
            ]
            
        logger.debug("Suggestions: %s", suggestions[:2])
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error("Suggestions generation failed: %s", str(e), exc_info=True)
        raise

# Related questions agent
def related_questions_agent(state: AgentState) -> Dict[str, Any]:
    logger = logging.getLogger(__name__)
    logger.info("Related questions agent started for query: %s", state["query"])
    try:
        prompt = f"""
        Based on the topic "{state['query']}", generate 5 related questions that someone might want to ask next.
        These should be natural follow-up questions that explore different aspects of the topic.
        Return ONLY the list of questions, one per line, with no additional text.
        """
        response = research_llm.invoke([HumanMessage(content=prompt)])
        
        questions_text = response.content.strip()
        questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
        
        if len(questions) > 5:
            questions = questions[:5]
        while len(questions) < 5:
            questions.append(f"What are the benefits of {state['query']}?")
            
        logger.info("Related questions generation completed")
        logger.debug("Related questions: %s", questions[:2])
        return {"related_questions": questions}
    except Exception as e:
        logger.error("Related questions generation failed: %s", str(e), exc_info=True)
        raise

# Workflow orchestration
def research_workflow(query: str) -> Dict[str, Any]:
    workflow_graph = StateGraph(AgentState)
    
    workflow_graph.add_node("research_node", research_agent)
    workflow_graph.add_node("definition_node", definition_agent)
    workflow_graph.add_node("suggestions_node", suggestions_agent) 
    workflow_graph.add_node("related_questions_node", related_questions_agent)
    
    workflow_graph.set_entry_point("research_node")
    
    workflow_graph.add_edge("research_node", "definition_node")
    workflow_graph.add_edge("definition_node", "suggestions_node")
    workflow_graph.add_edge("suggestions_node", "related_questions_node")
    workflow_graph.add_edge("related_questions_node", END)
    
    compiled_app = workflow_graph.compile()
    result = compiled_app.invoke({
        "query": query,
        "research_data": [],
        "definition": "",
        "suggestions": [],
        "related_questions": []
    })
    
    return {
        "definition": result["definition"],
        "suggestions": result["suggestions"],
        "relatedQuestions": result["related_questions"]
    }