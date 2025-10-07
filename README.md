# 🌊 ImageFlow - HTML to Image API

**"Transform your HTML into stunning images with the flow of a single API call"**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Playwright](https://img.shields.io/badge/Playwright-1.40+-red.svg)](https://playwright.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📖 Description

**ImageFlow** is a powerful, lightning-fast API that seamlessly converts HTML content into high-quality images. Whether you're building dynamic reports, generating social media previews, creating thumbnails, or capturing web content as images, ImageFlow delivers pixel-perfect results with enterprise-grade reliability.

## ✨ Key Features

- **🌐 Universal HTML Support** - Convert any HTML, CSS, and JavaScript into beautiful images
- **🖼️ External Image Integration** - Seamlessly load images from any URL with smart validation
- **📐 Flexible Dimensions** - Customize width, height, and output formats (PNG, JPEG)
- **🔐 API Key Authentication** - Secure your API with Bearer token authentication
- **🔒 Security First** - Built-in format validation and size limits (500MB max per image)
- **⚡ Lightning Fast** - Powered by Playwright's headless browser technology
- **🎯 Developer Friendly** - Simple REST API with comprehensive documentation
- **🌍 Any Domain Support** - Works with images from Google Drive, Imgur, CDNs, and more

## 🚀 Perfect For

- **Social Media Tools** - Generate preview images for links and content
- **Report Generation** - Convert HTML reports to shareable images
- **Thumbnail Creation** - Generate thumbnails for web content
- **Documentation** - Create visual guides and tutorials
- **E-commerce** - Generate product images from HTML descriptions
- **Newsletters** - Convert HTML emails to image previews

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- Chromium browser (installed via Playwright)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/imageflow.git
   cd imageflow
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browser**
   ```bash
   playwright install chromium
   ```

4. **Set up API Key (Optional)**
   ```bash
   export API_KEY="your-secure-api-key-here"
   ```

5. **Run the API**
   ```bash
   python app.py
   ```

The API will be available at `http://localhost:8000`

**Default API Key:** `imageflow-default-key-2024` (change this in production!)

## 📡 API Usage

### Convert HTML to Image

**Endpoint:** `POST /convert`

**Authentication:** Bearer token required in Authorization header

**Request Headers:**
```
Authorization: Bearer your-api-key-here
Content-Type: application/json
```

**Request Body:**
```json
{
  "html": "<html><body><h1>Hello World!</h1></body></html>",
  "width": 1920,
  "height": 1080,
  "format": "png",
  "quality": 90
}
```

**Parameters:**
- `html` (required): HTML content to convert
- `width` (optional): Image width in pixels (default: 1920)
- `height` (optional): Image height in pixels (default: 1080)
- `format` (optional): Output format - "png" or "jpeg" (default: "png")
- `quality` (optional): Image quality 1-100 (default: 90)

**Response:** Binary image data with appropriate content-type header.

### Example with curl

```bash
curl -X POST "http://localhost:8000/convert" \
  -H "Authorization: Bearer imageflow-default-key-2024" \
  -H "Content-Type: application/json" \
  -d '{
    "html": "<html><body style=\"background: linear-gradient(45deg, #ff6b6b, #4ecdc4); color: white; font-family: Arial; text-align: center; padding: 50px;\"><h1>Hello ImageFlow!</h1><p>Beautiful gradient background!</p></body></html>",
    "width": 800,
    "height": 600,
    "format": "png"
  }' \
  --output image.png
```

### External Image Support

ImageFlow supports external images from any domain:

```bash
curl -X POST "http://localhost:8000/convert" \
  -H "Authorization: Bearer imageflow-default-key-2024" \
  -H "Content-Type: application/json" \
  -d '{
    "html": "<html><body><h1>External Image Test</h1><img src=\"https://via.placeholder.com/400x300\" alt=\"Test Image\"></body></html>",
    "width": 800,
    "height": 600,
    "format": "png"
  }' \
  --output external_image.png
```

## 🔧 API Endpoints

- `GET /` - API information (no authentication required)
- `POST /convert` - Convert HTML to image (authentication required)
- `GET /health` - Health check (no authentication required)
- `GET /docs` - Interactive API documentation (Swagger UI)

## 🔐 Authentication

ImageFlow uses Bearer token authentication for the `/convert` endpoint:

- **Default API Key**: `imageflow-default-key-2024`
- **Environment Variable**: Set `API_KEY` to your custom key
- **Header Format**: `Authorization: Bearer your-api-key`
- **Security**: Change the default key in production!

## 🔒 Security Features

- **Format Validation**: Only allows safe image formats (jpg, jpeg, png, gif, webp, svg, bmp, ico)
- **Size Limits**: Maximum 500MB per external image
- **Content Type Validation**: Validates both URL extension and HTTP content-type headers
- **Sandboxed Processing**: All external content is processed safely in Playwright's browser

## 🌍 Supported External Image Sources

- Google Drive (both view and download URLs)
- Imgur
- CDNs (Cloudinary, AWS S3, etc.)
- Placeholder services (via.placeholder.com)
- Any publicly accessible image URL

## 📊 Performance

- **Fast Processing**: Typically converts HTML to image in 1-3 seconds
- **Memory Efficient**: Processes images in browser memory without disk storage
- **Concurrent Support**: Handles multiple requests simultaneously
- **Timeout Protection**: 30-second timeout prevents hanging requests

## 🐳 Docker Support

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium

COPY . .
EXPOSE 8000

CMD ["python", "app.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Visit `/docs` endpoint for interactive API documentation
- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Join community discussions in GitHub Discussions

## 💡 Why ImageFlow?

Just like water flows naturally, ImageFlow makes HTML-to-image conversion effortless. No complex setup, no learning curve - just send your HTML and receive beautiful images in return. It's the smooth, reliable solution that developers trust for their most important projects.

---

**Ready to make your HTML flow into images? Get started with ImageFlow today!** 🚀