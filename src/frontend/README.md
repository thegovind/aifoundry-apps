# Frontend - AIfoundry.app

Modern React frontend for the AIfoundry.app platform built with Vite, TypeScript, and Tailwind CSS.

## Features

- **React 18** - Modern React with hooks and concurrent features
- **TypeScript** - Type-safe development experience
- **Vite** - Fast build tool with hot module replacement
- **Tailwind CSS** - Utility-first CSS framework
- **Radix UI** - Accessible, unstyled UI components
- **Lucide React** - Beautiful and consistent icons
- **Agent Templates UI** - Browse and interact with AI agent templates
- **Pattern Customization** - Visual interface for multi-agent pattern configuration

## Prerequisites

- [Node.js 18+](https://nodejs.org/)
- [pnpm](https://pnpm.io/) - Fast, disk space efficient package manager

## Development Setup

### 1. Install Dependencies
```bash
# Install all dependencies using pnpm
pnpm install
```

### 2. Start Development Server
```bash
# Start the Vite development server
pnpm run dev
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Hot Reload**: Automatic browser refresh on code changes

### 3. Build for Production
```bash
# Create optimized production build
pnpm run build
```

### 4. Preview Production Build
```bash
# Preview the production build locally
pnpm run preview
```

## Available Scripts

- `pnpm run dev` - Start development server with hot reload
- `pnpm run build` - Create production build
- `pnpm run preview` - Preview production build locally
- `pnpm run lint` - Run ESLint for code quality
- `pnpm run lint:fix` - Fix auto-fixable ESLint issues

## Project Structure

```
src/frontend/
├── src/
│   ├── components/          # React components
│   │   ├── ui/             # Reusable UI components (Radix UI based)
│   │   ├── LandingPage.tsx # Main landing page
│   │   ├── TemplatesPage.tsx # Templates gallery
│   │   ├── SpecsPage.tsx   # Specifications management
│   │   └── ...             # Other feature components
│   ├── hooks/              # Custom React hooks
│   ├── lib/                # Utility functions
│   ├── assets/             # Static assets
│   ├── App.tsx            # Main application component
│   ├── main.tsx           # Application entry point
│   └── index.css          # Global styles
├── public/                 # Public static files
├── components.json         # Radix UI configuration
├── tailwind.config.js     # Tailwind CSS configuration
├── vite.config.ts         # Vite configuration
├── tsconfig.json          # TypeScript configuration
├── package.json           # Dependencies and scripts
├── pnpm-lock.yaml        # Locked dependency versions
└── README.md             # This file
```

## Key Technologies

### UI Framework
- **React 18** - Component-based UI library
- **TypeScript** - Static type checking
- **Tailwind CSS** - Utility-first styling
- **Radix UI** - Accessible component primitives

### Build Tools
- **Vite** - Fast build tool and dev server
- **PostCSS** - CSS processing
- **ESLint** - Code linting and formatting

### State Management
- React hooks for local state
- Context API for global state
- Custom hooks for data fetching

## Environment Variables

Create a `.env.local` file for local development:

```bash
# Backend API URL
VITE_API_URL=http://localhost:8000

# Other environment-specific variables
VITE_APP_NAME=AIfoundry.app
```

## API Integration

The frontend communicates with the FastAPI backend through:

- `GET /api/templates` - Fetch agent templates
- `GET /api/specs` - Fetch agent specifications  
- `GET /api/featured` - Fetch featured templates
- `GET /healthz` - Backend health check

## Component Architecture

### UI Components (`src/components/ui/`)
Reusable, accessible components based on Radix UI:
- `Button`, `Card`, `Dialog`, `Input`, etc.
- Consistent styling with Tailwind CSS
- Full TypeScript support

### Feature Components
- `LandingPage` - Main homepage with hero section
- `TemplatesPage` - Browse agent templates
- `SpecsPage` - Manage agent specifications
- `PatternWorkbench` - Customize multi-agent patterns

## Styling

### Tailwind CSS
- Utility-first CSS framework
- Responsive design out of the box
- Dark mode support (planned)
- Custom design system via `tailwind.config.js`

### Component Styling
- CSS-in-JS via Tailwind classes
- Consistent spacing and typography
- Accessible color contrast
- Mobile-first responsive design

## Testing

```bash
# Run tests (when test suite is added)
pnpm run test

# Run tests in watch mode
pnpm run test:watch

# Generate coverage report
pnpm run test:coverage
```

## Docker Development

The frontend is containerized for consistent deployment:

### Build Docker Image
```bash
docker build -t aifoundry-apps-frontend .
```

### Run Docker Container
```bash
docker run -p 3000:80 aifoundry-apps-frontend
```

## Deployment

The frontend is designed for deployment on:
- **Azure Container Apps** (primary)
- **Vercel** (alternative)
- **Netlify** (alternative)
- **Static hosting** (GitHub Pages, etc.)

See the [deployment guide](../../deployment/README.md) for detailed instructions.

## Performance Optimization

- **Code Splitting** - Automatic route-based splitting
- **Tree Shaking** - Dead code elimination
- **Asset Optimization** - Image and bundle optimization
- **Lazy Loading** - Components loaded on demand

## Contributing

1. Install dependencies: `pnpm install`
2. Start development server: `pnpm run dev`
3. Make your changes
4. Run linting: `pnpm run lint`
5. Build to test: `pnpm run build`
6. Submit a pull request

## Browser Support

- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Edge (latest 2 versions)

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.