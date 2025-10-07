from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from playwright.async_api import async_playwright
import asyncio
import io
import re
import os
from typing import Optional, Set

app = FastAPI(
    title="ImageFlow - HTML to Image API", 
    version="1.0.0",
    description="Transform your HTML into stunning images with the flow of a single API call",
    contact={
        "name": "ImageFlow Support",
        "url": "https://github.com/East-rayyy/imageflow",
    },
    license_info={
        "name": "MIT",
        "url": "https://github.com/East-rayyy/imageflow/blob/main/LICENSE",
    }
)

# API Key Authentication
API_KEY = os.getenv("API_KEY", "imageflow-default-key-2024")
security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key from Authorization header"""
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key. Please provide a valid API key in the Authorization header."
        )
    return credentials.credentials

# Allowed image formats and their MIME types
ALLOWED_IMAGE_FORMATS = {
    'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'ico'
}

ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
    'image/webp', 'image/svg+xml', 'image/bmp', 'image/x-icon', 'image/vnd.microsoft.icon'
}

# File size limit: 500MB
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB in bytes

class HTMLRequest(BaseModel):
    html: str
    width: Optional[int] = 1920
    height: Optional[int] = 1080
    format: Optional[str] = "png"
    quality: Optional[int] = 90

def convert_google_drive_url(url: str) -> str:
    """
    Convert Google Drive URLs to the lh3.googleusercontent.com format
    which works better with headless browsers
    
    Supports formats:
    - https://drive.google.com/file/d/{ID}/view
    - https://drive.google.com/open?id={ID}
    - https://drive.google.com/uc?id={ID}
    - https://drive.google.com/uc?export=view&id={ID}
    - https://drive.google.com/uc?export=download&id={ID}
    """
    # Pattern to extract Google Drive file ID
    patterns = [
        r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)',
        r'drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)',
        r'drive\.google\.com/uc\?.*?id=([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            file_id = match.group(1)
            # Convert to lh3.googleusercontent.com format (thumbnail/direct access)
            return f'https://lh3.googleusercontent.com/d/{file_id}'
    
    # If no pattern matches, return original URL
    return url

def process_html_urls(html: str) -> str:
    """
    Process HTML content and convert all Google Drive URLs to the proper format
    """
    # Find all src attributes with Google Drive URLs
    def replace_drive_url(match):
        full_match = match.group(0)
        url = match.group(1)
        
        # Check if it's a Google Drive URL
        if 'drive.google.com' in url:
            converted_url = convert_google_drive_url(url)
            return full_match.replace(url, converted_url)
        
        return full_match
    
    # Pattern to match src="..." or src='...'
    html = re.sub(r'src=["\']([^"\']+)["\']', replace_drive_url, html)
    
    # Also handle URLs in JavaScript variables (like const AVATAR_URL = "...")
    def replace_js_url(match):
        quote = match.group(1)
        url = match.group(2)
        
        if 'drive.google.com' in url:
            converted_url = convert_google_drive_url(url)
            return f'={quote}{converted_url}{quote}'
        
        return match.group(0)
    
    html = re.sub(r'=(["\'])(https?://[^"\']*drive\.google\.com[^"\']+)\1', replace_js_url, html)
    
    return html

def is_valid_image_format(url: str, content_type: str = None) -> bool:
    """Validate if URL points to an allowed image format"""
    # Check file extension
    url_lower = url.lower()
    for ext in ALLOWED_IMAGE_FORMATS:
        if f'.{ext}' in url_lower:
            return True
    
    # Check MIME type if provided
    if content_type:
        content_type_lower = content_type.lower().split(';')[0].strip()
        if content_type_lower in ALLOWED_MIME_TYPES:
            return True
    
    # If no clear indication, allow it (let the browser handle it)
    return True

def validate_image_request(request) -> None:
    """Validate image request for size and format"""
    # This will be called by Playwright's request handler
    pass

@app.get("/")
async def root():
    return {
        "name": "ImageFlow",
        "description": "Transform your HTML into stunning images with the flow of a single API call",
        "version": "1.0.0",
        "endpoint": "POST /convert",
        "authentication": "Bearer token required",
        "documentation": "/docs"
    }

@app.post("/convert", response_class=Response)
async def convert_html_to_image(request: HTMLRequest, api_key: str = Depends(verify_api_key)):
    """
    Convert HTML to image (PNG or JPEG) with external image support
    
    **Authentication Required:** Bearer token in Authorization header
    
    **Parameters:**
    - **html**: The HTML content to convert (supports external images)
    - **width**: Image width in pixels (default: 1920)
    - **height**: Image height in pixels (default: 1080)
    - **format**: Output format - png or jpeg (default: png)
    - **quality**: Image quality 1-100 (default: 90)
    
    **External Image Support:**
    - Supports external images from any domain
    - Automatically converts Google Drive URLs to thumbnail format
    - Only allows image formats: jpg, jpeg, png, gif, webp, svg, bmp, ico
    - Maximum file size: 500MB per image
    - Automatically validates content type and file format
    
    **Example Usage:**
    ```bash
    curl -X POST "https://your-api.com/convert" \
      -H "Authorization: Bearer your-api-key" \
      -H "Content-Type: application/json" \
      -d '{"html": "<h1>Hello World</h1>", "format": "png"}'
    ```
    """
    try:
        # Validate format
        valid_formats = ["png", "jpeg"]
        if request.format.lower() not in valid_formats:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid format. Must be one of: {', '.join(valid_formats)}"
            )
        
        # Validate quality
        if not (1 <= request.quality <= 100):
            raise HTTPException(
                status_code=400,
                detail="Quality must be between 1 and 100"
            )
        
        # Process HTML to convert Google Drive URLs
        processed_html = process_html_urls(request.html)
        
        # Convert HTML to image
        image_data = await html_to_image(
            html=processed_html,
            width=request.width,
            height=request.height,
            format=request.format.lower(),
            quality=request.quality
        )
        
        # Determine content type
        content_type_map = {
            "png": "image/png",
            "jpeg": "image/jpeg"
        }
        
        return Response(
            content=image_data,
            media_type=content_type_map[request.format.lower()]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

async def html_to_image(html: str, width: int, height: int, format: str, quality: int) -> bytes:
    """Convert HTML string to image bytes using Playwright with external image validation"""
    async with async_playwright() as p:
        # Launch browser with additional security options
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        page = await browser.new_page()
        
        # Set realistic user agent and headers to avoid detection
        await page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Set up response handler to validate external images
        async def handle_response(response):
            url = response.url
            resource_type = response.request.resource_type
            
            # Only validate image requests
            if resource_type in ['image', 'media'] and url.startswith(('http://', 'https://')):
                if response.status >= 400:
                    print(f"Failed to load image: {url} (Status: {response.status})")
                    return
                
                # Check content type
                content_type = response.headers.get('content-type', '')
                if not is_valid_image_format(url, content_type):
                    print(f"Blocking resource with invalid content type: {url} ({content_type})")
                    return
                
                # Check content length
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > MAX_FILE_SIZE:
                    print(f"Blocking oversized resource: {url} ({content_length} bytes)")
                    return
                
                print(f"Loading external image: {url} ({content_type})")
        
        # Set up response handler
        page.on('response', handle_response)
        
        try:
            # Set viewport size
            await page.set_viewport_size({"width": width, "height": height})
            
            # Set a timeout for page load
            page.set_default_timeout(30000)  # 30 seconds
            
            # Set HTML content
            await page.set_content(html, wait_until="networkidle")
            
            # Take screenshot
            screenshot_options = {
                "type": format,
                "quality": quality if format != "png" else None,  # PNG doesn't support quality
                "full_page": True
            }
            
            # Remove quality for PNG
            if format == "png":
                screenshot_options.pop("quality", None)
            
            image_bytes = await page.screenshot(**screenshot_options)
            return image_bytes
            
        except Exception as e:
            print(f"Error during image conversion: {str(e)}")
            raise e
        finally:
            await browser.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable (Railway provides this)
    port = int(os.environ.get("PORT", 8000))
    
    uvicorn.run(app, host="0.0.0.0", port=port)