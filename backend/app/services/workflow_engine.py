from sqlmodel import Session, select
from app.models import Workflow, Document
from app.routers import webhooks # Placeholder if we had internal webhook logic
# import requests # for external webhooks

class WorkflowEngine:
    def __init__(self, session: Session):
        self.session = session

    async def trigger_document_uploaded(self, document: Document):
        # Find matching workflows
        statement = select(Workflow).where(Workflow.is_active == True)
        workflows = self.session.exec(statement).all()
        
        for workflow in workflows:
            if workflow.trigger.get("type") == "DOCUMENT_UPLOADED":
                # Check filters (e.g. filename pattern)
                filters = workflow.trigger.get("filters", {})
                if self._check_filters(document, filters):
                    await self._execute_actions(workflow.actions, document)

    def _check_filters(self, document: Document, filters: dict) -> bool:
        # Simple filter logic
        if "filename_contains" in filters:
            if filters["filename_contains"] not in document.filename:
                return False
        return True

    async def _execute_actions(self, actions: list[dict], document: Document):
        for action in actions:
            action_type = action.get("type")
            if action_type == "WEBHOOK":
                url = action.get("url")
                if url:
                    # requests.post(url, json={"document_id": str(document.id), "status": document.status})
                    print(f"Triggering webhook to {url} for doc {document.id}")
            elif action_type == "EXTRACT_TOTAL":
                print(f"Running extract total for doc {document.id}")
