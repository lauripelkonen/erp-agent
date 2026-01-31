"""
Request models for the API endpoints.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class AttachmentData(BaseModel):
    """Attachment data from the frontend."""
    filename: str
    data: str = Field(..., description="Base64 encoded file data")
    mime_type: Optional[str] = None


class CreateOfferRequest(BaseModel):
    """Request model for creating a new offer from form data."""
    sender: str = Field(..., description="Customer email address")
    subject: str = Field(..., description="Email subject or offer title")
    body: str = Field(..., description="Email body or offer description")
    attachments: List[AttachmentData] = Field(
        default_factory=list,
        description="List of attachments with base64 encoded data"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "sender": "customer@company.com",
                "subject": "Quote request for products",
                "body": "Please provide a quote for:\n- 10x Product A\n- 5x Product B",
                "attachments": []
            }
        }


class SendToERPRequest(BaseModel):
    """Request model for sending an approved offer to ERP."""
    line_ids: List[str] = Field(
        ...,
        description="List of line IDs to include in the ERP offer"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "line_ids": ["line-1", "line-2", "line-3"]
            }
        }
