from pydantic import BaseModel, EmailStr, Field


class ContactSupportRequest(BaseModel):
    """Payload for contacting Attendeely support from the dashboard or mobile app."""

    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=3, max_length=150)
    message: str = Field(..., min_length=10, max_length=2000)

{
  "cells": [],
  "metadata": {
    "language_info": {
      "name": "python"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 2
}