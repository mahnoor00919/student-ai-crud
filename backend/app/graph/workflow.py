# from __future__ import annotations

# import json
# import logging
# import re
# from typing import Any, Dict, List, Optional

# from fastapi import HTTPException  # type: ignore[import-not-found]
# from langchain_core.messages import (  # type: ignore[import-not-found]
#     HumanMessage,
#     SystemMessage,
# )
# from langchain_openai import ChatOpenAI  # type: ignore[import-not-found]

# from ..config import get_settings
# from ..tools.crud_tools import CRUDTools
# from .schemas import (
#     ExtractedFields,
#     GraphState,
#     IntentResult,
#     IntentType,
# )

# logger = logging.getLogger(__name__)


# # ============================================================
# # LLM SYSTEM PROMPT
# # ============================================================

# SYSTEM_PROMPT = """
# You are the intent-understanding AI for a Student Record Management System.

# Your job is to understand NATURAL LANGUAGE from the user and convert it
# into a structured CRUD intent.

# Do NOT require the user to use a specific command format.

# The user may use casual, conversational, incomplete, or differently
# worded English.

# The available student fields are:

# - student_id: database ID
# - name: student's current/existing name
# - roll_number: student's roll number
# - age: student's age
# - email: student's email
# - new_name: new name when updating
# - new_roll_number: new roll number when updating
# - new_age: new age when updating
# - new_email: new email when updating
# - confirmed: whether the user confirmed a destructive operation

# ============================================================
# CREATE
# ============================================================

# Use CREATE when the user wants to add/register/create a student.

# Examples:

# "create a student named mano with roll number 9"
# "add a new student"
# "register Ali, roll number 12, age 20, email ali@gmail.com"
# "I want to add a student called Sara"

# For CREATE:
# - name should contain the student's name
# - roll_number should contain the roll number
# - age should contain the age
# - email should contain the email

# Required fields for CREATE:
# name, roll_number, age, email

# If any are missing, return them in missing_fields.

# ============================================================
# READ
# ============================================================

# Use READ when the user wants information about ONE student.

# Examples:

# "show student 1"
# "get student with id 1"
# "find student with roll number 9"
# "show me mano"
# "what are the details of student 1"

# Use:
# student_id when an ID is provided.
# roll_number when a roll number is provided.
# name when a name is provided.

# ============================================================
# READ_ALL
# ============================================================

# Use READ_ALL when the user wants multiple/all students.

# Examples:

# "show all students"
# "list students"
# "give me all student records"
# "who are the students?"
# "display everyone"

# ============================================================
# UPDATE
# ============================================================

# Use UPDATE whenever the user wants to CHANGE, EDIT, MODIFY, RENAME,
# CORRECT, or UPDATE an existing student's information.

# Natural language is allowed.

# Examples:

# "update student 1 name to mahnoor"
# "change student 1's name to mahnoor"
# "edit student 1 and change the name to mahnoor"
# "rename student 1 to mahnoor"
# "I want to change the name of student 1 to mahnoor"
# "make student 1's name mahnoor"
# "student 1 should now be called mahnoor"
# "change mano's name to mahnoor"
# "update mano's email to new@gmail.com"
# "change student 1's age to 21"
# "correct student 1's roll number to 15"

# IMPORTANT UPDATE RULE:

# The person/student being modified goes into:
# - student_id OR
# - name OR
# - roll_number

# The NEW value goes into:
# - new_name
# - new_roll_number
# - new_age
# - new_email

# For example:

# User:
# "change student 1's name to mahnoor"

# Return conceptually:

# intent = UPDATE
# student_id = 1
# new_name = "mahnoor"

# DO NOT put "mahnoor" into the name field.

# Another example:

# User:
# "rename mano to mahnoor"

# Return conceptually:

# intent = UPDATE
# name = "mano"
# new_name = "mahnoor"

# Another example:

# User:
# "change student 1's age to 21"

# Return:

# intent = UPDATE
# student_id = 1
# new_age = 21

# Another example:

# User:
# "update student 1 email to mahnoor@gmail.com"

# Return:

# intent = UPDATE
# student_id = 1
# new_email = "mahnoor@gmail.com"

# The user does NOT need to say the exact phrase "update student".

# ============================================================
# DELETE
# ============================================================

# Use DELETE when the user wants to remove/delete a student.

# Examples:

# "delete student 1"
# "remove student with id 1"
# "delete mano"
# "I don't need student 1 anymore"

# Deletion must require confirmation.

# Do not actually delete until confirmed is true.

# ============================================================
# CONFIRM DELETE
# ============================================================

# Use CONFIRM_DELETE when the user confirms a previously requested deletion.

# Examples:

# "yes"
# "yes delete it"
# "confirm"
# "do it"
# "delete him"
# "yes, go ahead"

# ============================================================
# CLARIFY
# ============================================================

# Use CLARIFY only when the request cannot safely be completed because
# important information is genuinely missing.

# Do NOT ask for clarification when the user's natural-language request
# already contains enough information.

# For example:

# "change student 1's name to mahnoor"

# has enough information.

# It should NOT be CLARIFY.

# ============================================================
# CHITCHAT
# ============================================================

# Use CHITCHAT for greetings or casual conversation that is unrelated
# to student CRUD operations.

# ============================================================
# IMPORTANT
# ============================================================

# Understand the meaning of the user's sentence, not its exact wording.

# Never require a rigid command syntax.

# If the user's request contains enough information to perform the operation,
# extract it directly.
# """


# # ============================================================
# # LLM
# # ============================================================

# def _get_llm() -> ChatOpenAI:
#     settings = get_settings()

#     return ChatOpenAI(
#         model=settings.openai_model,
#         api_key=settings.openai_api_key,
#         base_url=settings.openai_base_url,
#         temperature=0,
#         max_tokens=1000,
#     )


# def _get_structured_llm():
#     """
#     Ask LangChain/OpenAI-compatible provider to return an IntentResult
#     instead of relying only on prompt instructions to produce JSON.
#     """
#     llm = _get_llm()

#     return llm.with_structured_output(
#         IntentResult
#     )


# # ============================================================
# # JSON FALLBACK
# # ============================================================

# def _parse_intent(raw_content: Any) -> IntentResult:
#     """
#     Fallback parser for providers/models that return raw JSON text.
#     """

#     if raw_content is None:
#         return IntentResult(
#             intent=IntentType.UNKNOWN,
#             confidence=0.0,
#             raw_summary="Empty response from AI",
#         )

#     if not isinstance(raw_content, str):
#         raw_content = str(raw_content)

#     content = raw_content.strip()

#     # Remove markdown code fences
#     content = re.sub(r"```json\s*", "", content, flags=re.IGNORECASE)
#     content = re.sub(r"```\s*", "", content)

#     # First attempt: complete response is JSON
#     try:
#         data = json.loads(content)
#         return IntentResult.model_validate(data)
#     except Exception:
#         pass

#     # Second attempt: find a JSON object
#     start = content.find("{")
#     end = content.rfind("}")

#     if start != -1 and end != -1 and end > start:
#         candidate = content[start:end + 1]

#         try:
#             data = json.loads(candidate)
#             return IntentResult.model_validate(data)
#         except Exception:
#             pass

#     logger.error(
#         "Failed to parse intent JSON. Raw response: %r",
#         content,
#     )

#     return IntentResult(
#         intent=IntentType.UNKNOWN,
#         confidence=0.0,
#         raw_summary="The AI returned an invalid intent response.",
#         clarification_question=(
#             "I couldn't understand the request. "
#             "Please try saying what you want to do with the student."
#         ),
#     )


# # ============================================================
# # INTENT EXTRACTION
# # ============================================================

# def extract_intent(state: GraphState) -> GraphState:
#     """
#     Convert natural language into IntentResult.
#     """

#     user_message = state.user_message.strip()

#     history_text = ""

#     if state.messages:
#         recent_messages = state.messages[-8:]

#         history_text = "\n".join(
#             f"{message.get('role', 'user')}: "
#             f"{message.get('content', '')}"
#             for message in recent_messages
#         )

#     prompt = f"""
# Conversation history:
# {history_text}

# Current user message:
# {user_message}

# Understand the user's INTENT and extract all relevant student fields.

# Pay special attention to UPDATE requests.

# For example:

# "update student 1 name to mahnoor"

# means:

# UPDATE
# student_id = 1
# new_name = "mahnoor"

# Do not ask the user to rewrite their request in a specific format.
# """

#     # --------------------------------------------------------
#     # PRIMARY: structured output
#     # --------------------------------------------------------

#     try:
#         structured_llm = _get_structured_llm()

#         response = structured_llm.invoke(
#             [
#                 SystemMessage(content=SYSTEM_PROMPT),
#                 HumanMessage(content=prompt),
#             ]
#         )

#         if isinstance(response, IntentResult):
#             intent_result = response
#         else:
#             intent_result = IntentResult.model_validate(response)

#         logger.info(
#             "STRUCTURED INTENT: %s",
#             intent_result.model_dump(),
#         )

#         state.intent_result = intent_result
#         state.missing_fields = list(intent_result.missing_fields)

#         return state

#     except Exception as structured_error:
#         logger.exception(
#             "Structured intent extraction failed: %s",
#             structured_error,
#         )

#     # --------------------------------------------------------
#     # FALLBACK: normal model response + JSON parser
#     # --------------------------------------------------------

#     try:
#         llm = _get_llm()

#         response = llm.invoke(
#             [
#                 SystemMessage(
#                     content=SYSTEM_PROMPT
#                     + """

# Return ONLY a valid JSON object matching the IntentResult schema.
# Do not explain your reasoning.
# """
#                 ),
#                 HumanMessage(content=prompt),
#             ]
#         )

#         content = response.content

#         intent_result = _parse_intent(content)

#         state.intent_result = intent_result
#         state.missing_fields = list(intent_result.missing_fields)

#         return state

#     except Exception as fallback_error:
#         logger.exception(
#             "Fallback intent extraction failed: %s",
#             fallback_error,
#         )

#         state.intent_result = IntentResult(
#             intent=IntentType.UNKNOWN,
#             confidence=0.0,
#             clarification_question=(
#                 "I couldn't understand the request. Please try again."
#             ),
#         )

#         state.missing_fields = []

#         return state


# # ============================================================
# # MERGE PENDING OPERATIONS
# # ============================================================

# def merge_pending(state: GraphState) -> GraphState:
#     """
#     Merge the current request with a previous operation that was waiting
#     for missing information or confirmation.
#     """

#     intent = state.intent_result

#     if intent is None:
#         return state

#     pending = state.pending_operation

#     if not pending:
#         return state

#     pending_type = pending.get("intent")

#     # --------------------------------------------------------
#     # CREATE waiting for missing fields
#     # --------------------------------------------------------

#     if pending_type == IntentType.CREATE.value:

#         if intent.intent == IntentType.CREATE:

#             old_fields = pending.get("fields", {})
#             new_fields = intent.fields.model_dump(exclude_none=True)

#             merged_fields = {
#                 **old_fields,
#                 **new_fields,
#             }

#             intent.fields = ExtractedFields.model_validate(
#                 merged_fields
#             )

#             required_fields = [
#                 "name",
#                 "roll_number",
#                 "age",
#                 "email",
#             ]

#             missing = [
#                 field
#                 for field in required_fields
#                 if getattr(intent.fields, field) is None
#             ]

#             intent.missing_fields = missing

#             state.missing_fields = missing

#             if not missing:
#                 state.pending_operation = None

#         return state

#     # --------------------------------------------------------
#     # DELETE waiting for confirmation
#     # --------------------------------------------------------

#     if pending_type == IntentType.DELETE.value:

#         if intent.intent == IntentType.CONFIRM_DELETE:
#             intent.intent = IntentType.DELETE
#             intent.fields = ExtractedFields.model_validate(
#                 pending.get("fields", {})
#             )
#             intent.fields.confirmed = True

#             state.missing_fields = []
#             state.pending_operation = None

#         elif intent.intent == IntentType.DELETE:
#             # User may have repeated the delete request.
#             state.pending_operation = pending

#         return state

#     return state


# # ============================================================
# # ROUTING
# # ============================================================

# def route_after_intent(state: GraphState) -> str:
#     intent = state.intent_result

#     if intent is None:
#         return "clarification"

#     if intent.intent == IntentType.CLARIFY:
#         return "clarification"

#     if intent.intent == IntentType.UNKNOWN:
#         return "clarification"

#     if intent.intent == IntentType.CHITCHAT:
#         return "clarification"

#     if intent.intent == IntentType.DELETE:
#         fields = intent.fields

#         if not fields.confirmed:
#             return "delete_confirmation"

#     if intent.missing_fields:
#         return "clarification"

#     if intent.intent == IntentType.CREATE:
#         return "create"

#     if intent.intent == IntentType.READ:
#         return "read"

#     if intent.intent == IntentType.READ_ALL:
#         return "read_all"

#     if intent.intent == IntentType.UPDATE:
#         return "update"

#     if intent.intent == IntentType.DELETE:
#         return "delete"

#     return "clarification"


# # ============================================================
# # CLARIFICATION
# # ============================================================

# def ask_clarification(state: GraphState) -> GraphState:
#     intent = state.intent_result

#     if intent is None:
#         state.response = (
#             "I couldn't understand the request. Please try again."
#         )
#         return state

#     if intent.clarification_question:
#         state.response = intent.clarification_question
#         return state

#     missing = intent.missing_fields

#     if intent.intent == IntentType.CREATE:

#         labels = {
#             "name": "the student's name",
#             "roll_number": "the roll number",
#             "age": "the age",
#             "email": "the email address",
#         }

#         readable = [
#             labels.get(field, field)
#             for field in missing
#         ]

#         if len(readable) == 1:
#             state.response = (
#                 f"Could you please provide {readable[0]}?"
#             )

#         else:
#             state.response = (
#                 "Could you please provide "
#                 + ", ".join(readable[:-1])
#                 + " and "
#                 + readable[-1]
#                 + "?"
#             )

#         return state

#     if intent.intent == IntentType.UPDATE:

#         state.response = (
#             "Which student would you like to update, and "
#             "what information should I change?"
#         )

#         return state

#     if intent.intent == IntentType.DELETE:

#         state.response = (
#             "Which student would you like to delete?"
#         )

#         return state

#     state.response = (
#         "Could you please clarify what you would like me to do?"
#     )

#     return state


# # ============================================================
# # CREATE
# # ============================================================

# def create_student(state: GraphState) -> GraphState:
#     tools = state.tools

#     if tools is None:
#         state.response = "CRUD tools are not available."
#         return state

#     fields = state.intent_result.fields

#     try:
#         result = tools.create_student(
#             name=fields.name,
#             roll_number=fields.roll_number,
#             age=fields.age,
#             email=fields.email,
#         )

#         state.tool_result = result

#         if result.get("success"):
#             student = result.get("student", result)

#             state.response = (
#                 f"Student '{student.get('name', fields.name)}' "
#                 f"(roll {student.get('roll_number', fields.roll_number)}) "
#                 f"created successfully. "
#                 f"Details: "
#                 f"ID={student.get('id')}, "
#                 f"Name={student.get('name')}, "
#                 f"Roll={student.get('roll_number')}, "
#                 f"Age={student.get('age')}, "
#                 f"Email={student.get('email')}"
#             )
#         else:
#             state.response = result.get(
#                 "message",
#                 "The student could not be created.",
#             )

#     except HTTPException as e:
#         state.response = str(e.detail)

#     except Exception:
#         logger.exception("CREATE failed")
#         state.response = (
#             "I couldn't create the student because an error occurred."
#         )

#     return state


# # ============================================================
# # READ
# # ============================================================

# def read_student(state: GraphState) -> GraphState:
#     tools = state.tools

#     if tools is None:
#         state.response = "CRUD tools are not available."
#         return state

#     fields = state.intent_result.fields

#     try:
#         result = tools.get_student(
#             student_id=fields.student_id,
#             roll_number=fields.roll_number,
#             name=fields.name,
#         )

#         state.tool_result = result

#         if result.get("success"):
#             student = result.get("student", result)

#             state.response = (
#                 f"Student found: "
#                 f"ID={student.get('id')}, "
#                 f"Name={student.get('name')}, "
#                 f"Roll={student.get('roll_number')}, "
#                 f"Age={student.get('age')}, "
#                 f"Email={student.get('email')}"
#             )
#         else:
#             state.response = result.get(
#                 "message",
#                 "Student not found.",
#             )

#     except HTTPException as e:
#         state.response = str(e.detail)

#     except Exception:
#         logger.exception("READ failed")
#         state.response = (
#             "I couldn't retrieve the student because an error occurred."
#         )

#     return state


# # ============================================================
# # READ ALL
# # ============================================================

# def read_all_students(state: GraphState) -> GraphState:
#     tools = state.tools

#     if tools is None:
#         state.response = "CRUD tools are not available."
#         return state

#     try:
#         result = tools.get_students()

#         state.tool_result = result

#         students = result.get("students", [])

#         if not students:
#             state.response = "There are currently no students."
#             return state

#         lines = ["Here are the students:"]

#         for student in students:
#             lines.append(
#                 f"ID={student.get('id')}, "
#                 f"Name={student.get('name')}, "
#                 f"Roll={student.get('roll_number')}, "
#                 f"Age={student.get('age')}, "
#                 f"Email={student.get('email')}"
#             )

#         state.response = "\n".join(lines)

#     except Exception:
#         logger.exception("READ_ALL failed")
#         state.response = (
#             "I couldn't retrieve the students because an error occurred."
#         )

#     return state


# # ============================================================
# # UPDATE
# # ============================================================

# def update_student(state: GraphState) -> GraphState:
#     tools = state.tools

#     if tools is None:
#         state.response = "CRUD tools are not available."
#         return state

#     fields = state.intent_result.fields

#     logger.info(
#         "UPDATE fields: %s",
#         fields.model_dump(),
#     )

#     # We need either an ID, current name, or roll number
#     if (
#         fields.student_id is None
#         and fields.name is None
#         and fields.roll_number is None
#     ):
#         state.response = (
#             "Which student would you like to update?"
#         )
#         return state

#     # We also need something to change
#     if (
#         fields.new_name is None
#         and fields.new_roll_number is None
#         and fields.new_age is None
#         and fields.new_email is None
#     ):
#         state.response = (
#             "What information would you like to change?"
#         )
#         return state

#     try:
#         result = tools.update_student(
#             student_id=fields.student_id,
#             roll_number=fields.roll_number,
#             name=fields.name,
#             new_name=fields.new_name,
#             new_roll_number=fields.new_roll_number,
#             new_age=fields.new_age,
#             new_email=fields.new_email,
#         )

#         state.tool_result = result

#         if result.get("success"):
#             student = result.get("student", result)

#             state.response = (
#                 f"Student updated successfully. "
#                 f"Details: "
#                 f"ID={student.get('id')}, "
#                 f"Name={student.get('name')}, "
#                 f"Roll={student.get('roll_number')}, "
#                 f"Age={student.get('age')}, "
#                 f"Email={student.get('email')}"
#             )
#         else:
#             state.response = result.get(
#                 "message",
#                 "The student could not be updated.",
#             )

#     except HTTPException as e:
#         state.response = str(e.detail)

#     except Exception:
#         logger.exception("UPDATE failed")
#         state.response = (
#             "I couldn't update the student because an error occurred."
#         )

#     return state


# # ============================================================
# # DELETE CONFIRMATION
# # ============================================================

# def delete_confirmation(state: GraphState) -> GraphState:
#     fields = state.intent_result.fields

#     state.pending_operation = {
#         "intent": IntentType.DELETE.value,
#         "fields": fields.model_dump(exclude_none=True),
#     }

#     identifier = ""

#     if fields.student_id is not None:
#         identifier = f"ID {fields.student_id}"

#     elif fields.roll_number is not None:
#         identifier = f"roll number {fields.roll_number}"

#     elif fields.name is not None:
#         identifier = f"name '{fields.name}'"

#     state.response = (
#         f"Are you sure you want to delete the student with "
#         f"{identifier}? Please confirm with 'yes' or 'confirm'."
#     )

#     return state


# # ============================================================
# # DELETE
# # ============================================================

# def delete_student(state: GraphState) -> GraphState:
#     tools = state.tools

#     if tools is None:
#         state.response = "CRUD tools are not available."
#         return state

#     fields = state.intent_result.fields

#     try:
#         result = tools.delete_student(
#             student_id=fields.student_id,
#             roll_number=fields.roll_number,
#             name=fields.name,
#             confirm=True,
#         )

#         state.tool_result = result
#         state.pending_operation = None

#         if result.get("success"):
#             state.response = result.get(
#                 "message",
#                 "Student deleted successfully.",
#             )
#         else:
#             state.response = result.get(
#                 "message",
#                 "The student could not be deleted.",
#             )

#     except HTTPException as e:
#         state.response = str(e.detail)

#     except Exception:
#         logger.exception("DELETE failed")
#         state.response = (
#             "I couldn't delete the student because an error occurred."
#         )

#     return state


# # ============================================================
# # GRAPH
# # ============================================================

# def build_graph():
#     from langgraph.graph import (  # type: ignore[import-not-found]
#         END,
#         START,
#         StateGraph,
#     )

#     graph = StateGraph(GraphState)

#     graph.add_node("extract_intent", extract_intent)
#     graph.add_node("merge_pending", merge_pending)
#     graph.add_node("clarification", ask_clarification)
#     graph.add_node("create", create_student)
#     graph.add_node("read", read_student)
#     graph.add_node("read_all", read_all_students)
#     graph.add_node("update", update_student)
#     graph.add_node("delete_confirmation", delete_confirmation)
#     graph.add_node("delete", delete_student)

#     graph.add_edge(START, "extract_intent")
#     graph.add_edge("extract_intent", "merge_pending")

#     graph.add_conditional_edges(
#         "merge_pending",
#         route_after_intent,
#         {
#             "clarification": "clarification",
#             "create": "create",
#             "read": "read",
#             "read_all": "read_all",
#             "update": "update",
#             "delete_confirmation": "delete_confirmation",
#             "delete": "delete",
#         },
#     )

#     graph.add_edge("clarification", END)
#     graph.add_edge("create", END)
#     graph.add_edge("read", END)
#     graph.add_edge("read_all", END)
#     graph.add_edge("update", END)
#     graph.add_edge("delete_confirmation", END)
#     graph.add_edge("delete", END)

#     return graph.compile()


# # ============================================================
# # COMPILED GRAPH
# # ============================================================

# _compiled_graph = None


# def get_compiled_graph():
#     global _compiled_graph

#     if _compiled_graph is None:
#         _compiled_graph = build_graph()

#     return _compiled_graph


# # ============================================================
# # SIMPLE CONVERSATION STORE
# # ============================================================

# _conversation_store: Dict[str, GraphState] = {}


# # ============================================================
# # RUN CHAT
# # ============================================================
# def run_chat(
#     user_message: str,
#     db,
#     thread_id: str = "default",
# ):

#     tools = CRUDTools(db)

#     previous = _conversation_store.get(thread_id)

#     if previous:
#         state = GraphState(
#             messages=list(previous.messages),
#             pending_operation=previous.pending_operation,
#             thread_id=thread_id,
#             user_message=user_message,
#             tools=tools,
#         )
#     else:
#         state = GraphState(
#             thread_id=thread_id,
#             user_message=user_message,
#             tools=tools,
#         )

#     state.messages.append(
#         {
#             "role": "user",
#             "content": user_message,
#         }
#     )

#     graph = get_compiled_graph()

#     result_state = graph.invoke(state)

#     # LangGraph may return a dictionary or GraphState
#     if isinstance(result_state, dict):
#         result_state = GraphState.model_validate(result_state)

#     # Save conversation history
#     messages = list(result_state.messages)

#     messages.append(
#         {
#             "role": "assistant",
#             "content": result_state.response,
#         }
#     )

#     saved_state = GraphState(
#         messages=messages[-20:],
#         pending_operation=result_state.pending_operation,
#         thread_id=thread_id,
#     )

#     _conversation_store[thread_id] = saved_state

#     # IMPORTANT:
#     # ai.py expects a dictionary because it does:
#     # ChatResponse(**result)
#     return {
#         "response": result_state.response,
#         "intent": (
#             result_state.intent_result.intent.value
#             if result_state.intent_result
#             else None
#         ),
#         "needs_clarification": result_state.needs_clarification,
#         "pending_operation": result_state.pending_operation,
#     }


# def clear_thread(thread_id: str = "default") -> None:
#     """
#     Clear the stored conversation for a thread.
#     """
#     _conversation_store.pop(thread_id, None)

# def clear_thread(thread_id: str = "default") -> None:
#     """
#     Clear the stored conversation for a thread.
#     """
#     _conversation_store.pop(thread_id, None)


from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict

from fastapi import HTTPException  # type: ignore[import-not-found]
from langchain_core.messages import (  # type: ignore[import-not-found]
    HumanMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI  # type: ignore[import-not-found]

from ..config import get_settings
from ..tools.crud_tools import CRUDTools
from .schemas import (
    ExtractedFields,
    GraphState,
    IntentResult,
    IntentType,
)

logger = logging.getLogger(__name__)


# ============================================================
# LLM SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are the intent-understanding AI for a Student Record Management System.

Your job is to understand NATURAL LANGUAGE and convert it into a
structured CRUD intent.

Do NOT require exact command syntax.

The user may speak casually, conversationally, or use different
wording.

Available fields:

- student_id
- name
- roll_number
- age
- email
- new_name
- new_roll_number
- new_age
- new_email
- confirmed


============================================================
CREATE
============================================================

Use CREATE when the user wants to add/register/create a student.

Examples:

"create a student named Mano with roll number 9"
"add a new student"
"register Ali, roll number 12, age 20, email ali@gmail.com"
"I want to add Sara"

For CREATE:

name = student's name
roll_number = student's roll number
age = student's age
email = student's email

Required:

name
roll_number
age
email

If information is missing, put the missing fields in missing_fields.


============================================================
READ
============================================================

Use READ when the user wants information about ONE student.

Examples:

"show student 1"
"get student with id 1"
"find student with roll number 9"
"show me Mano"
"what are the details of student 1"

Use:

student_id for database ID
roll_number for roll number
name for student's name


============================================================
READ_ALL
============================================================

Use READ_ALL when the user wants multiple/all students.

Examples:

"show all students"
"list students"
"give me all student records"
"who are the students?"
"display everyone"


============================================================
UPDATE
============================================================

Use UPDATE whenever the user wants to:

change
edit
modify
rename
correct
update

an existing student.

The student being modified goes into:

student_id OR name OR roll_number

The NEW value goes into:

new_name
new_roll_number
new_age
new_email

Examples:

"change student 1's name to Mahnoor"

means:

intent = UPDATE
student_id = 1
new_name = "Mahnoor"

"rename Mano to Mahnoor"

means:

intent = UPDATE
name = "Mano"
new_name = "Mahnoor"

"change student 1's age to 21"

means:

intent = UPDATE
student_id = 1
new_age = 21

"update student 1 email to mahnoor@gmail.com"

means:

intent = UPDATE
student_id = 1
new_email = "mahnoor@gmail.com"

Do NOT put the new value into the old/current field.

For example:

"change student 1's name to Mahnoor"

MUST NOT become:

name = "Mahnoor"

It must become:

student_id = 1
new_name = "Mahnoor"


============================================================
DELETE
============================================================

Use DELETE when the user wants to remove a student.

Examples:

"delete student 1"
"remove student with id 1"
"delete roll no 9"
"remove Mano"
"I don't need student 1 anymore"

Use the identifier supplied by the user:

student_id
OR
roll_number
OR
name

Deletion requires confirmation.

Never set confirmed=true for the initial delete request.


============================================================
CONFIRM DELETE
============================================================

Use CONFIRM_DELETE when the user confirms a previously requested
deletion.

Examples:

"yes"
"yes delete it"
"confirm"
"do it"
"yes, go ahead"
"delete him"


============================================================
IMPORTANT
============================================================

Understand the MEANING of the user's sentence.

Do not require exact command syntax.

Extract all information explicitly provided by the user.

Do not invent missing values.
"""


# ============================================================
# LLM
# ============================================================

def _get_llm() -> ChatOpenAI:
    settings = get_settings()

    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=0,
        max_tokens=1000,
    )


def _get_structured_llm():
    llm = _get_llm()

    return llm.with_structured_output(IntentResult)


# ============================================================
# HELPERS
# ============================================================

def _is_confirmation_message(message: str) -> bool:
    """
    Deterministically recognize common confirmation replies.

    This is intentionally NOT left entirely to the LLM.
    """

    normalized = message.strip().lower()

    confirmation_patterns = {
        "yes",
        "y",
        "yes please",
        "yes, please",
        "confirm",
        "confirmed",
        "do it",
        "go ahead",
        "yes go ahead",
        "yes, go ahead",
        "delete it",
        "delete him",
        "delete her",
        "sure",
        "okay",
        "ok",
    }

    return normalized in confirmation_patterns


def _is_cancel_message(message: str) -> bool:
    """
    Recognize common cancellation responses.
    """

    normalized = message.strip().lower()

    cancellation_patterns = {
        "no",
        "n",
        "cancel",
        "cancel it",
        "don't",
        "do not",
        "stop",
        "never mind",
        "nevermind",
    }

    return normalized in cancellation_patterns


# ============================================================
# JSON FALLBACK
# ============================================================

def _parse_intent(raw_content: Any) -> IntentResult:

    if raw_content is None:
        return IntentResult(
            intent=IntentType.UNKNOWN,
            confidence=0.0,
            raw_summary="Empty response from AI",
        )

    if not isinstance(raw_content, str):
        raw_content = str(raw_content)

    content = raw_content.strip()

    content = re.sub(
        r"```json\s*",
        "",
        content,
        flags=re.IGNORECASE,
    )

    content = re.sub(
        r"```\s*",
        "",
        content,
    )

    try:
        data = json.loads(content)
        return IntentResult.model_validate(data)

    except Exception:
        pass

    start = content.find("{")
    end = content.rfind("}")

    if start != -1 and end != -1 and end > start:

        candidate = content[start:end + 1]

        try:
            data = json.loads(candidate)
            return IntentResult.model_validate(data)

        except Exception:
            pass

    logger.error(
        "Failed to parse intent JSON. Raw response: %r",
        content,
    )

    return IntentResult(
        intent=IntentType.UNKNOWN,
        confidence=0.0,
        raw_summary="Invalid AI response.",
        clarification_question=(
            "I couldn't understand the request. "
            "Please tell me what you want to do with the student."
        ),
    )


# ============================================================
# INTENT EXTRACTION
# ============================================================

def extract_intent(state: GraphState) -> GraphState:

    user_message = state.user_message.strip()

    # --------------------------------------------------------
    # IMPORTANT:
    # If we are waiting for DELETE confirmation, do NOT ask
    # the LLM to reinterpret "yes".
    # --------------------------------------------------------

    if (
        state.pending_operation
        and state.pending_operation.get("intent")
        == IntentType.DELETE.value
    ):

        if _is_confirmation_message(user_message):

            state.intent_result = IntentResult(
                intent=IntentType.CONFIRM_DELETE,
                fields=ExtractedFields(
                    confirmed=True
                ),
                confidence=1.0,
                raw_summary="User confirmed pending deletion.",
            )

            state.missing_fields = []

            logger.info(
                "DELETE CONFIRMATION detected deterministically."
            )

            return state

        if _is_cancel_message(user_message):

            state.intent_result = IntentResult(
                intent=IntentType.CHITCHAT,
                confidence=1.0,
                raw_summary="User cancelled deletion.",
            )

            state.missing_fields = []

            return state

    # --------------------------------------------------------
    # Normal LLM extraction
    # --------------------------------------------------------

    history_text = ""

    if state.messages:

        recent_messages = state.messages[-8:]

        history_text = "\n".join(
            f"{message.get('role', 'user')}: "
            f"{message.get('content', '')}"
            for message in recent_messages
        )

    prompt = f"""
Conversation history:

{history_text}

Current user message:

{user_message}

Understand the user's intent and extract ALL relevant fields.

Pay special attention to UPDATE.

Example:

"change student 1's name to Mahnoor"

means:

intent = UPDATE
student_id = 1
new_name = "Mahnoor"

Another example:

"delete roll no 9"

means:

intent = DELETE
roll_number = 9

Do not require a rigid command format.
"""

    # --------------------------------------------------------
    # PRIMARY: structured output
    # --------------------------------------------------------

    try:

        structured_llm = _get_structured_llm()

        response = structured_llm.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]
        )

        if isinstance(response, IntentResult):
            intent_result = response
        else:
            intent_result = IntentResult.model_validate(response)

        logger.info(
            "STRUCTURED INTENT: %s",
            intent_result.model_dump(),
        )

        state.intent_result = intent_result
        state.missing_fields = list(
            intent_result.missing_fields
        )

        return state

    except Exception as structured_error:

        logger.exception(
            "Structured intent extraction failed: %s",
            structured_error,
        )

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    try:

        llm = _get_llm()

        response = llm.invoke(
            [
                SystemMessage(
                    content=SYSTEM_PROMPT
                    + """

Return ONLY a valid JSON object matching the IntentResult schema.
Do not explain your reasoning.
"""
                ),
                HumanMessage(content=prompt),
            ]
        )

        intent_result = _parse_intent(
            response.content
        )

        state.intent_result = intent_result

        state.missing_fields = list(
            intent_result.missing_fields
        )

        return state

    except Exception as fallback_error:

        logger.exception(
            "Fallback intent extraction failed: %s",
            fallback_error,
        )

        state.intent_result = IntentResult(
            intent=IntentType.UNKNOWN,
            confidence=0.0,
            clarification_question=(
                "I couldn't understand the request. "
                "Please try again."
            ),
        )

        state.missing_fields = []

        return state


# ============================================================
# MERGE PENDING OPERATIONS
# ============================================================

def merge_pending(state: GraphState) -> GraphState:

    intent = state.intent_result

    if intent is None:
        return state

    pending = state.pending_operation

    if not pending:
        return state

    pending_type = pending.get("intent")

    # ========================================================
    # DELETE CONFIRMATION
    # ========================================================

    if pending_type == IntentType.DELETE.value:

        # ----------------------------------------------------
        # User confirmed
        # ----------------------------------------------------

        if intent.intent == IntentType.CONFIRM_DELETE:

            original_fields = pending.get(
                "fields",
                {},
            )

            restored_fields = ExtractedFields.model_validate(
                original_fields
            )

            restored_fields.confirmed = True

            state.intent_result = IntentResult(
                intent=IntentType.DELETE,
                fields=restored_fields,
                confidence=1.0,
                raw_summary=(
                    "Confirmed deletion using "
                    "the original pending operation."
                ),
            )

            state.missing_fields = []

            # Do NOT remove this before delete executes.
            # Keep it available until delete_student finishes.

            return state

        # ----------------------------------------------------
        # User cancelled
        # ----------------------------------------------------

        if _is_cancel_message(
            state.user_message
        ):

            state.pending_operation = None

            state.intent_result = IntentResult(
                intent=IntentType.CHITCHAT,
                confidence=1.0,
                raw_summary="Deletion cancelled.",
            )

            state.response = (
                "Okay, I cancelled the deletion."
            )

            return state

        # ----------------------------------------------------
        # User repeats another DELETE request
        # ----------------------------------------------------

        if intent.intent == IntentType.DELETE:

            return state

        return state

    # ========================================================
    # CREATE PENDING OPERATION
    # ========================================================

    if pending_type == IntentType.CREATE.value:

        old_fields = pending.get(
            "fields",
            {},
        )

        new_fields = (
            intent.fields.model_dump(
                exclude_none=True
            )
        )

        merged_fields = {
            **old_fields,
            **new_fields,
        }

        intent.fields = ExtractedFields.model_validate(
            merged_fields
        )

        required_fields = [
            "name",
            "roll_number",
            "age",
            "email",
        ]

        missing = [
            field
            for field in required_fields
            if getattr(
                intent.fields,
                field,
            ) is None
        ]

        intent.missing_fields = missing
        state.missing_fields = missing

        if not missing:
            state.pending_operation = None

        return state

    return state


# ============================================================
# ROUTING
# ============================================================

def route_after_intent(state: GraphState) -> str:

    intent = state.intent_result

    if intent is None:
        return "clarification"

    # Cancelled deletion
    if (
        intent.intent == IntentType.CHITCHAT
        and state.response
    ):
        return "clarification"

    if intent.intent == IntentType.UNKNOWN:
        return "clarification"

    if intent.intent == IntentType.CLARIFY:
        return "clarification"

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    if intent.intent == IntentType.DELETE:

        fields = intent.fields

        # We need an identifier.
        if (
            fields.student_id is None
            and fields.roll_number is None
            and fields.name is None
        ):
            return "clarification"

        if not fields.confirmed:
            return "delete_confirmation"

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    if intent.intent == IntentType.CREATE:

        if intent.missing_fields:
            return "clarification"

        return "create"

    # --------------------------------------------------------
    # READ
    # --------------------------------------------------------

    if intent.intent == IntentType.READ:

        fields = intent.fields

        if (
            fields.student_id is None
            and fields.roll_number is None
            and fields.name is None
        ):
            state.response = (
                "Which student would you like me to find?"
            )

            return "clarification"

        return "read"

    # --------------------------------------------------------
    # READ ALL
    # --------------------------------------------------------

    if intent.intent == IntentType.READ_ALL:
        return "read_all"

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    if intent.intent == IntentType.UPDATE:
        return "update"

    return "clarification"


# ============================================================
# CLARIFICATION
# ============================================================

def ask_clarification(state: GraphState) -> GraphState:

    intent = state.intent_result

    if intent is None:

        state.needs_clarification = True

        state.response = (
            "I couldn't understand the request. "
            "Please try again."
        )

        return state

    # If another function already generated a response,
    # don't overwrite it.

    if state.response:

        state.needs_clarification = True

        return state

    if intent.clarification_question:

        state.needs_clarification = True

        state.response = (
            intent.clarification_question
        )

        return state

    missing = intent.missing_fields

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    if intent.intent == IntentType.CREATE:

        labels = {
            "name": "the student's name",
            "roll_number": "the roll number",
            "age": "the age",
            "email": "the email address",
        }

        readable = [
            labels.get(field, field)
            for field in missing
        ]

        if len(readable) == 1:

            state.response = (
                f"Could you please provide "
                f"{readable[0]}?"
            )

        elif readable:

            state.response = (
                "Could you please provide "
                + ", ".join(readable[:-1])
                + " and "
                + readable[-1]
                + "?"
            )

        else:

            state.response = (
                "Could you please provide "
                "the missing student information?"
            )

        state.needs_clarification = True

        # Save pending CREATE operation.
        state.pending_operation = {
            "intent": IntentType.CREATE.value,
            "fields": intent.fields.model_dump(
                exclude_none=True
            ),
        }

        return state

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    if intent.intent == IntentType.UPDATE:

        state.needs_clarification = True

        fields = intent.fields

        if (
            fields.student_id is None
            and fields.name is None
            and fields.roll_number is None
        ):

            state.response = (
                "Which student would you like to update?"
            )

        elif (
            fields.new_name is None
            and fields.new_roll_number is None
            and fields.new_age is None
            and fields.new_email is None
        ):

            state.response = (
                "What information would you like to change?"
            )

        return state

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    if intent.intent == IntentType.DELETE:

        state.needs_clarification = True

        state.response = (
            "Which student would you like to delete? "
            "Please provide the student ID, roll number, "
            "or name."
        )

        return state

    # --------------------------------------------------------
    # DEFAULT
    # --------------------------------------------------------

    state.needs_clarification = True

    state.response = (
        "Could you please clarify what you would like "
        "me to do?"
    )

    return state


# ============================================================
# CREATE
# ============================================================

def create_student(state: GraphState) -> GraphState:

    tools = state.tools

    if tools is None:

        state.response = (
            "CRUD tools are not available."
        )

        return state

    fields = state.intent_result.fields

    try:

        result = tools.create_student(
            name=fields.name,
            roll_number=fields.roll_number,
            age=fields.age,
            email=fields.email,
        )

        state.tool_result = result

        if result.get("success"):

            student = result.get(
                "student",
                result,
            )

            state.response = (
                f"Student '{student.get('name')}' "
                f"(roll {student.get('roll_number')}) "
                f"created successfully. "
                f"Details: "
                f"ID={student.get('id')}, "
                f"Name={student.get('name')}, "
                f"Roll={student.get('roll_number')}, "
                f"Age={student.get('age')}, "
                f"Email={student.get('email')}"
            )

            state.pending_operation = None

        else:

            state.response = result.get(
                "message",
                "The student could not be created.",
            )

    except HTTPException as e:

        state.response = str(e.detail)

    except Exception:

        logger.exception("CREATE failed")

        state.response = (
            "I couldn't create the student "
            "because an error occurred."
        )

    return state


# ============================================================
# READ
# ============================================================

def read_student(state: GraphState) -> GraphState:

    tools = state.tools

    if tools is None:

        state.response = (
            "CRUD tools are not available."
        )

        return state

    fields = state.intent_result.fields

    try:

        result = tools.get_student(
            student_id=fields.student_id,
            roll_number=fields.roll_number,
            name=fields.name,
        )

        state.tool_result = result

        if result.get("success"):

            student = result.get(
                "student",
                result,
            )

            state.response = (
                "Student found: "
                f"ID={student.get('id')}, "
                f"Name={student.get('name')}, "
                f"Roll={student.get('roll_number')}, "
                f"Age={student.get('age')}, "
                f"Email={student.get('email')}"
            )

        else:

            state.response = result.get(
                "message",
                "Student not found.",
            )

    except HTTPException as e:

        state.response = str(e.detail)

    except Exception:

        logger.exception("READ failed")

        state.response = (
            "I couldn't retrieve the student "
            "because an error occurred."
        )

    return state


# ============================================================
# READ ALL
# ============================================================

def read_all_students(state: GraphState) -> GraphState:

    tools = state.tools

    if tools is None:

        state.response = (
            "CRUD tools are not available."
        )

        return state

    try:

        result = tools.get_students()

        state.tool_result = result

        students = result.get(
            "students",
            [],
        )

        if not students:

            state.response = (
                "There are currently no students."
            )

            return state

        lines = [
            "Here are the students:"
        ]

        for student in students:

            lines.append(
                f"ID={student.get('id')}, "
                f"Name={student.get('name')}, "
                f"Roll={student.get('roll_number')}, "
                f"Age={student.get('age')}, "
                f"Email={student.get('email')}"
            )

        state.response = "\n".join(lines)

    except Exception:

        logger.exception(
            "READ_ALL failed"
        )

        state.response = (
            "I couldn't retrieve the students "
            "because an error occurred."
        )

    return state


# ============================================================
# UPDATE
# ============================================================

def update_student(state: GraphState) -> GraphState:

    tools = state.tools

    if tools is None:

        state.response = (
            "CRUD tools are not available."
        )

        return state

    fields = state.intent_result.fields

    logger.info(
        "UPDATE fields: %s",
        fields.model_dump(),
    )

    # Need student identifier
    if (
        fields.student_id is None
        and fields.name is None
        and fields.roll_number is None
    ):

        state.needs_clarification = True

        state.response = (
            "Which student would you like to update?"
        )

        return state

    # Need something to change
    if (
        fields.new_name is None
        and fields.new_roll_number is None
        and fields.new_age is None
        and fields.new_email is None
    ):

        state.needs_clarification = True

        state.response = (
            "What information would you like to change?"
        )

        return state

    try:

        result = tools.update_student(
            student_id=fields.student_id,
            roll_number=fields.roll_number,
            name=fields.name,
            new_name=fields.new_name,
            new_roll_number=fields.new_roll_number,
            new_age=fields.new_age,
            new_email=fields.new_email,
        )

        state.tool_result = result

        if result.get("success"):

            student = result.get(
                "student",
                result,
            )

            state.response = (
                "Student updated successfully. "
                "Details: "
                f"ID={student.get('id')}, "
                f"Name={student.get('name')}, "
                f"Roll={student.get('roll_number')}, "
                f"Age={student.get('age')}, "
                f"Email={student.get('email')}"
            )

        else:

            state.response = result.get(
                "message",
                "The student could not be updated.",
            )

    except HTTPException as e:

        state.response = str(e.detail)

    except Exception:

        logger.exception(
            "UPDATE failed"
        )

        state.response = (
            "I couldn't update the student "
            "because an error occurred."
        )

    return state


# ============================================================
# DELETE CONFIRMATION
# ============================================================

def delete_confirmation(
    state: GraphState,
) -> GraphState:

    fields = state.intent_result.fields

    # --------------------------------------------------------
    # Validate that we actually have an identifier
    # --------------------------------------------------------

    if (
        fields.student_id is None
        and fields.roll_number is None
        and fields.name is None
    ):

        state.needs_clarification = True

        state.response = (
            "Which student would you like to delete? "
            "Please provide the student ID, roll number, "
            "or name."
        )

        return state

    # --------------------------------------------------------
    # SAVE EXACT IDENTIFIER
    # --------------------------------------------------------

    state.pending_operation = {
        "intent": IntentType.DELETE.value,
        "fields": fields.model_dump(
            exclude_none=True
        ),
    }

    identifier = ""

    if fields.student_id is not None:

        identifier = (
            f"ID {fields.student_id}"
        )

    elif fields.roll_number is not None:

        identifier = (
            f"roll number {fields.roll_number}"
        )

    elif fields.name is not None:

        identifier = (
            f"name '{fields.name}'"
        )

    state.needs_clarification = False

    state.response = (
        "Are you sure you want to delete "
        f"the student with {identifier}? "
        "Please confirm with 'yes' or 'confirm'."
    )

    return state


# ============================================================
# DELETE
# ============================================================

def delete_student(state: GraphState) -> GraphState:

    tools = state.tools

    if tools is None:

        state.response = (
            "CRUD tools are not available."
        )

        return state

    fields = state.intent_result.fields

    logger.info(
        "DELETE fields: %s",
        fields.model_dump(),
    )

    # --------------------------------------------------------
    # IMPORTANT SAFETY CHECK
    # --------------------------------------------------------

    if (
        fields.student_id is None
        and fields.roll_number is None
        and fields.name is None
    ):

        state.response = (
            "I don't know which student you want to delete."
        )

        return state

    try:

        result = tools.delete_student(
            student_id=fields.student_id,
            roll_number=fields.roll_number,
            name=fields.name,
            confirm=True,
        )

        state.tool_result = result

        if result.get("success"):

            state.response = result.get(
                "message",
                "Student deleted successfully.",
            )

            state.pending_operation = None

        else:

            state.response = result.get(
                "message",
                "The student could not be deleted.",
            )

            # Keep pending operation if deletion failed.
            # This prevents losing the user's original
            # deletion request.

    except HTTPException as e:

        state.response = str(e.detail)

    except Exception:

        logger.exception(
            "DELETE failed"
        )

        state.response = (
            "I couldn't delete the student "
            "because an error occurred."
        )

    return state


# ============================================================
# GRAPH
# ============================================================

def build_graph():

    from langgraph.graph import (  # type: ignore[import-not-found]
        END,
        START,
        StateGraph,
    )

    graph = StateGraph(GraphState)

    graph.add_node(
        "extract_intent",
        extract_intent,
    )

    graph.add_node(
        "merge_pending",
        merge_pending,
    )

    graph.add_node(
        "clarification",
        ask_clarification,
    )

    graph.add_node(
        "create",
        create_student,
    )

    graph.add_node(
        "read",
        read_student,
    )

    graph.add_node(
        "read_all",
        read_all_students,
    )

    graph.add_node(
        "update",
        update_student,
    )

    graph.add_node(
        "delete_confirmation",
        delete_confirmation,
    )

    graph.add_node(
        "delete",
        delete_student,
    )

    graph.add_edge(
        START,
        "extract_intent",
    )

    graph.add_edge(
        "extract_intent",
        "merge_pending",
    )

    graph.add_conditional_edges(
        "merge_pending",
        route_after_intent,
        {
            "clarification": "clarification",
            "create": "create",
            "read": "read",
            "read_all": "read_all",
            "update": "update",
            "delete_confirmation": "delete_confirmation",
            "delete": "delete",
        },
    )

    graph.add_edge(
        "clarification",
        END,
    )

    graph.add_edge(
        "create",
        END,
    )

    graph.add_edge(
        "read",
        END,
    )

    graph.add_edge(
        "read_all",
        END,
    )

    graph.add_edge(
        "update",
        END,
    )

    graph.add_edge(
        "delete_confirmation",
        END,
    )

    graph.add_edge(
        "delete",
        END,
    )

    return graph.compile()


# ============================================================
# COMPILED GRAPH
# ============================================================

_compiled_graph = None


def get_compiled_graph():

    global _compiled_graph

    if _compiled_graph is None:

        _compiled_graph = build_graph()

    return _compiled_graph


# ============================================================
# CONVERSATION STORE
# ============================================================

_conversation_store: Dict[
    str,
    GraphState,
] = {}


# ============================================================
# RUN CHAT
# ============================================================

def run_chat(
    user_message: str,
    db,
    thread_id: str = "default",
):

    tools = CRUDTools(db)

    previous = _conversation_store.get(
        thread_id
    )

    if previous:

        state = GraphState(
            messages=list(
                previous.messages
            ),
            pending_operation=(
                previous.pending_operation
            ),
            thread_id=thread_id,
            user_message=user_message,
            tools=tools,
        )

    else:

        state = GraphState(
            thread_id=thread_id,
            user_message=user_message,
            tools=tools,
        )

    state.messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    graph = get_compiled_graph()

    result_state = graph.invoke(state)

    if isinstance(result_state, dict):

        result_state = GraphState.model_validate(
            result_state
        )

    # --------------------------------------------------------
    # Save conversation
    # --------------------------------------------------------

    messages = list(
        result_state.messages
    )

    messages.append(
        {
            "role": "assistant",
            "content": result_state.response,
        }
    )

    saved_state = GraphState(
        messages=messages[-20:],
        pending_operation=(
            result_state.pending_operation
        ),
        thread_id=thread_id,
    )

    _conversation_store[
        thread_id
    ] = saved_state

    # --------------------------------------------------------
    # Return dictionary for ai.py
    # --------------------------------------------------------

    return {
        "response": result_state.response,

        "intent": (
            result_state.intent_result.intent.value
            if result_state.intent_result
            else None
        ),

        "needs_clarification": (
            result_state.needs_clarification
        ),

        "pending_operation": (
            result_state.pending_operation
        ),
    }


# ============================================================
# CLEAR THREAD
# ============================================================

def clear_thread(
    thread_id: str = "default",
) -> None:

    _conversation_store.pop(
        thread_id,
        None,
    )