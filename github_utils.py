import requests
import base64
from typing import Optional
from datetime import datetime
import os
from config import Config

class GitHubStorage:
    def __init__(self):
        self.config = Config()
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.config.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def _get_repo_parts(self):
        """Extract owner and repo name from GITHUB_REPO"""
        if '/' not in self.config.GITHUB_REPO:
            raise ValueError("GITHUB_REPO should be in format 'owner/repo'")
        
        return self.config.GITHUB_REPO.split('/', 1)
    
    def upload_file(self, file_content: bytes, filename: str, folder: str = "documents") -> Optional[str]:
        """
        Upload file to GitHub repository
        Returns the download URL if successful, None otherwise
        """
        try:
            owner, repo = self._get_repo_parts()
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name, extension = os.path.splitext(filename)
            unique_filename = f"{base_name}_{timestamp}{extension}"
            
            # Create the file path
            file_path = f"{folder}/{unique_filename}" if folder else unique_filename
            
            # Encode file content to base64
            content_base64 = base64.b64encode(file_content).decode('utf-8')
            
            # Prepare the API request
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}"
            
            data = {
                "message": f"Upload document: {filename}",
                "content": content_base64
            }
            
            # Check if file already exists (unlikely due to timestamp, but good practice)
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                # File exists, we need to provide the SHA for update
                existing_file = response.json()
                data["sha"] = existing_file["sha"]
            
            # Upload the file
            response = requests.put(url, headers=self.headers, json=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                return result["content"]["download_url"]
            else:
                print(f"Error uploading to GitHub: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            print(f"Error uploading file to GitHub: {str(e)}")
            return None
    
    def check_repository_access(self) -> bool:
        """
        Check if the repository exists and we have access to it
        """
        try:
            owner, repo = self._get_repo_parts()
            url = f"{self.base_url}/repos/{owner}/{repo}"
            
            response = requests.get(url, headers=self.headers)
            return response.status_code == 200
        
        except Exception as e:
            print(f"Error checking repository access: {str(e)}")
            return False
    
    def create_repository(self, private: bool = True) -> bool:
        """
        Create a new repository (if it doesn't exist)
        Note: This creates a repo under the authenticated user's account
        """
        try:
            owner, repo = self._get_repo_parts()
            
            # First check if repo already exists
            if self.check_repository_access():
                return True
            
            url = f"{self.base_url}/user/repos"
            
            data = {
                "name": repo,
                "description": "AI Document Processor - Document Storage",
                "private": private,
                "auto_init": True
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            return response.status_code == 201
        
        except Exception as e:
            print(f"Error creating repository: {str(e)}")
            return False
    
    def list_uploaded_files(self, folder: str = "documents", limit: int = 100) -> list:
        """
        List files uploaded to the repository
        """
        try:
            owner, repo = self._get_repo_parts()
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{folder}"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                files = response.json()
                if isinstance(files, list):
                    return files[:limit]
            
            return []
        
        except Exception as e:
            print(f"Error listing files: {str(e)}")
            return []
    
    def delete_file(self, file_path: str, sha: str) -> bool:
        """
        Delete a file from the repository
        """
        try:
            owner, repo = self._get_repo_parts()
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}"
            
            data = {
                "message": f"Delete file: {file_path}",
                "sha": sha
            }
            
            response = requests.delete(url, headers=self.headers, json=data)
            return response.status_code == 200
        
        except Exception as e:
            print(f"Error deleting file: {str(e)}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[dict]:
        """
        Get information about a specific file
        """
        try:
            owner, repo = self._get_repo_parts()
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
            
            return None
        
        except Exception as e:
            print(f"Error getting file info: {str(e)}")
            return None

def get_github_storage():
    """Factory function to get GitHub storage instance"""
    return GitHubStorage()
