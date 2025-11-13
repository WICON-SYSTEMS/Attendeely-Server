import cloudinary
import cloudinary.uploader
from app.core.config import settings
import logging
from typing import Optional
import base64
import io

logger = logging.getLogger(__name__)

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)


class CloudinaryService:
    """Service for uploading images to Cloudinary"""
    
    @staticmethod
    async def upload_logo(file_content: bytes, filename: str, organization_id: int) -> Optional[str]:
        """
        Upload organization logo to Cloudinary
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            organization_id: Organization ID for folder structure
            
        Returns:
            str: URL of uploaded image or None if failed
        """
        try:
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file_content,
                folder=f"attendeely/organizations/{organization_id}",
                public_id=f"logo_{organization_id}",
                overwrite=True,
                resource_type="image",
                transformation=[
                    {'width': 500, 'height': 500, 'crop': 'limit'},
                    {'quality': 'auto'},
                    {'fetch_format': 'auto'}
                ]
            )
            
            logger.info(f"Logo uploaded successfully for organization {organization_id}")
            return result.get('secure_url')
            
        except Exception as e:
            logger.error(f"Failed to upload logo for organization {organization_id}: {str(e)}")
            return None
    
    @staticmethod
    async def delete_logo(logo_url: str) -> bool:
        """
        Delete logo from Cloudinary
        
        Args:
            logo_url: URL of the logo to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            # Extract public_id from URL
            public_id = logo_url.split('/')[-1].split('.')[0]
            cloudinary.uploader.destroy(public_id)
            logger.info(f"Logo deleted successfully: {public_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete logo: {str(e)}")
            return False
    
    @staticmethod
    async def upload_employee_photo(file_content: bytes, filename: str, employee_id: int, organization_id: int) -> Optional[str]:
        """
        Upload employee photo to Cloudinary
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            employee_id: Employee ID for folder structure
            organization_id: Organization ID for folder structure
            
        Returns:
            str: URL of uploaded image or None if failed
        """
        try:
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file_content,
                folder=f"attendeely/organizations/{organization_id}/employees/{employee_id}",
                public_id=f"photo_{employee_id}",
                overwrite=True,
                resource_type="image",
                transformation=[
                    {'width': 400, 'height': 400, 'crop': 'fill', 'gravity': 'face'},
                    {'quality': 'auto'},
                    {'fetch_format': 'auto'}
                ]
            )
            
            logger.info(f"Employee photo uploaded successfully for employee {employee_id}")
            return result.get('secure_url')
            
        except Exception as e:
            logger.error(f"Failed to upload employee photo for employee {employee_id}: {str(e)}")
            return None
    
    @staticmethod
    async def delete_employee_photo(photo_url: str) -> bool:
        """
        Delete employee photo from Cloudinary
        
        Args:
            photo_url: URL of the photo to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            # Extract public_id from URL - need to handle full path
            # Cloudinary URLs format: https://res.cloudinary.com/cloud_name/image/upload/v1234567890/folder/photo_id.jpg
            parts = photo_url.split('/')
            # Find the index after 'upload' or 'v' version
            try:
                upload_index = next(i for i, part in enumerate(parts) if part == 'upload')
                # Get everything after upload (skip version if present)
                path_parts = parts[upload_index + 1:]
                if path_parts and path_parts[0].startswith('v'):
                    path_parts = path_parts[1:]
                public_id = '/'.join(path_parts).rsplit('.', 1)[0]  # Remove extension
            except (StopIteration, ValueError):
                # Fallback: extract from end of URL
                public_id = photo_url.split('/')[-1].split('.')[0]
            
            cloudinary.uploader.destroy(public_id)
            logger.info(f"Employee photo deleted successfully: {public_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete employee photo: {str(e)}")
            return False