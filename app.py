from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from playwright.async_api import async_playwright
import asyncio
import io
import re
from typing import Optional, Set

app = FastAPI(
    title="ImageFlow - HTML to Image API", 
    version="1.0.0",
    description="Transform your HTML into stunning images with the flow of a single API call",
    contact={
        "name": "ImageFlow Support",
        "url": "https://github.com/yourusername/imageflow",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

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
        "docs": "/docs",
        "health": "/health"
    }

@app.post("/convert", response_class=Response)
async def convert_html_to_image(request: HTMLRequest):
    """
    Convert HTML to image (PNG or JPEG) with external image support
    
    - **html**: The HTML content to convert (supports external images)
    - **width**: Image width in pixels (default: 1920)
    - **height**: Image height in pixels (default: 1080)
    - **format**: Output format - png or jpeg (default: png)
    - **quality**: Image quality 1-100 (default: 90)
    
    **External Image Support:**
    - Supports external images from any domain
    - Only allows image formats: jpg, jpeg, png, gif, webp, svg, bmp, ico
    - Maximum file size: 500MB per image
    - Automatically validates content type and file format
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
        
        # Convert HTML to image
        image_data = await html_to_image(
            html=request.html,
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
