# Saathii Backend API Documentation

This directory contains the Docusaurus-based documentation for the Saathii Backend API.

## 🚀 Quick Start

### Development

```bash
# Install dependencies
npm install

# Start development server
npm start

# Open http://localhost:3000
```

### Build

```bash
# Build for production
npm run build

# Serve built files
npm run serve
```

### Docker

```bash
# Build and run with Docker
docker-compose -f docker-compose.docs.yml up -d

# Access at http://localhost:3000
```

## 📁 Structure

```
docs/
├── docs/                    # Documentation content
│   ├── getting-started.md   # Getting started guide
│   ├── api/                 # API documentation
│   └── guides/              # Integration guides
├── src/
│   ├── components/          # React components
│   └── css/                 # Custom styles
├── static/                  # Static assets
├── docusaurus.config.ts     # Docusaurus configuration
├── sidebars.ts             # Sidebar configuration
└── package.json            # Dependencies
```

## 🔧 Configuration

### Environment Variables

- `NODE_ENV`: Environment (development/production)
- `BASE_URL`: Base URL for the documentation
- `API_URL`: Backend API URL for Swagger UI integration

### Customization

1. **Styling**: Edit `src/css/custom.css`
2. **Components**: Add React components in `src/components/`
3. **Configuration**: Modify `docusaurus.config.ts`
4. **Sidebar**: Update `sidebars.ts`

## 📝 Content Management

### Adding New Pages

1. Create a new `.md` file in the appropriate directory
2. Add frontmatter with metadata:
   ```markdown
   ---
   sidebar_position: 1
   title: Page Title
   description: Page description
   ---
   ```
3. Update `sidebars.ts` to include the new page

### API Documentation

API documentation is organized by feature:
- `api/authentication.md` - Authentication endpoints
- `api/user-management.md` - User management
- `api/call-management.md` - Call management
- `api/swagger-ui.md` - Interactive API explorer

### Integration Guides

Guides for different integration scenarios:
- `guides/installation.md` - Installation guide
- `guides/react-native-integration.md` - React Native integration
- `guides/api-examples.md` - API usage examples

## 🚀 Deployment

### GitHub Pages

The documentation is automatically deployed to GitHub Pages on push to main branch.

### Manual Deployment

```bash
# Build the documentation
npm run build

# Deploy to your hosting service
# Copy the build/ directory to your web server
```

### Docker Deployment

```bash
# Build Docker image
docker build -f Dockerfile.docs -t saathii-docs .

# Run container
docker run -d -p 3000:80 saathii-docs
```

## 🔍 Features

### Interactive API Explorer

- Embedded Swagger UI for testing endpoints
- Dark/light theme support
- Real-time API testing

### Real-time Updates

- WebSocket integration examples
- Live status updates
- Connection management

### Mobile-First Design

- Responsive layout
- Touch-friendly navigation
- Optimized for mobile devices

### Search

- Built-in search functionality
- Full-text search across all content
- Fast and accurate results

## 🛠️ Development

### Prerequisites

- Node.js 20+
- npm or yarn
- Git

### Setup

```bash
# Clone repository
git clone https://github.com/saathii/saathii-backend-api.git

# Navigate to docs directory
cd saathii-backend-api/docs

# Install dependencies
npm install

# Start development server
npm start
```

### Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm run serve` - Serve built files
- `npm run clear` - Clear cache
- `npm run typecheck` - TypeScript type checking

## 📚 Documentation Guidelines

### Writing Style

- Use clear, concise language
- Include code examples
- Provide step-by-step instructions
- Use consistent formatting

### Code Examples

- Include both cURL and JavaScript examples
- Show error handling
- Provide complete, working examples
- Use syntax highlighting

### Images and Diagrams

- Use Mermaid for diagrams
- Optimize images for web
- Include alt text for accessibility
- Use consistent styling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

### Content Guidelines

- Follow the existing structure
- Use consistent formatting
- Include examples
- Test all code snippets
- Update sidebar if needed

## 📞 Support

- **GitHub Issues**: [Report issues](https://github.com/saathii/saathii-backend-api/issues)
- **Discussions**: [Ask questions](https://github.com/saathii/saathii-backend-api/discussions)
- **Documentation**: Check the [API Documentation](./docs/getting-started)

## 📄 License

This documentation is part of the Saathii Backend API project and follows the same license terms.