# K8s Cost Optimizer Dashboard

Interactive React dashboard for visualizing Kubernetes cost optimization opportunities and managing recommendations.

## Features

- **Real-time Updates**: WebSocket connection for live cost data
- **Interactive Charts**: 5+ different chart types using Recharts
- **Multi-Cloud Support**: AWS, GCP, and Azure cluster visualization
- **Export Functionality**: CSV, Terraform, and YAML exports
- **Dark/Light Theme**: Full theme toggle support
- **Demo Mode**: Impressive sample data for testing
- **Responsive Design**: Mobile, tablet, and desktop support

## Technology Stack

- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **State Management**: Zustand
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Notifications**: React Hot Toast
- **Icons**: React Icons

## Getting Started

### Prerequisites

- Node.js 18+
- Docker (for containerized deployment)

### Development

```bash
# Install dependencies
cd services/dashboard
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The dashboard will be available at http://localhost:3000

### Docker Deployment

```bash
# Build Docker image
docker build -t k8s-optimizer-dashboard:latest .

# Run container
docker run -p 8080:80 k8s-optimizer-dashboard:latest
```

The dashboard will be available at http://localhost:8080

### Using Docker Compose

From the project root:

```bash
# Start all services including dashboard
docker-compose up -d

# Access dashboard
open http://localhost:8080
```

## Project Structure

```
services/dashboard/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── CostCard.jsx
│   │   └── SavingsChart.jsx
│   ├── pages/               # Page components
│   │   ├── Dashboard.jsx
│   │   ├── Clusters.jsx
│   │   ├── Workloads.jsx
│   │   ├── Recommendations.jsx
│   │   ├── Savings.jsx
│   │   └── Settings.jsx
│   ├── services/            # API and utility services
│   │   ├── api.js
│   │   ├── websocket.js
│   │   ├── export.js
│   │   └── calculations.js
│   ├── hooks/               # Custom React hooks
│   │   ├── useWebSocket.js
│   │   └── useTheme.js
│   ├── store/               # Zustand state management
│   │   └── index.js
│   ├── App.jsx              # Main application component
│   ├── main.jsx             # Application entry point
│   └── index.css            # Global styles
├── public/                  # Static assets
├── index.html               # HTML template
├── Dockerfile               # Multi-stage Docker build
├── nginx.conf               # Nginx configuration
├── package.json             # Dependencies and scripts
├── vite.config.js           # Vite configuration
├── tailwind.config.js       # Tailwind CSS configuration
└── postcss.config.js        # PostCSS configuration
```

## Pages

### Dashboard
Main overview page showing:
- Cost summary cards
- Savings trends (line chart)
- Cluster comparison (bar chart)
- Optimization types distribution (pie chart)
- Top recommendations list

### Clusters
Cluster management view with:
- Cluster cards showing workload count
- Current and optimized costs
- Potential savings per cluster
- Provider badges (AWS, GCP, Azure)

### Workloads
Workload list with:
- Sortable/filterable table
- Cluster filtering
- Optimization type badges
- Confidence scores
- Savings amounts

### Recommendations
Optimization recommendations view:
- Detailed recommendation cards
- Risk level indicators
- Confidence scores
- Apply action buttons
- Optimization type categorization

### Savings
Historical savings tracker showing:
- Monthly/yearly savings metrics
- Savings over time (line chart)
- Cost comparison (area chart)
- Savings percentage

### Settings
Configuration options:
- Theme toggle (light/dark)
- Demo mode toggle
- API URL configuration

## Features

### Real-Time Updates

The dashboard connects to the optimizer API via WebSocket for live updates:

```javascript
import { useWebSocket } from './hooks/useWebSocket';

const { connected, lastMessage } = useWebSocket();
```

Updates are received every 30 seconds and automatically refresh the UI.

### Chart Types

1. **Line Chart**: Savings trend over time
2. **Area Chart**: Current vs optimized cost comparison
3. **Bar Chart**: Cluster cost comparison
4. **Pie Chart**: Optimization types distribution
5. **Stacked Area**: Cost breakdown visualization

### Export Functionality

Export data in multiple formats:

- **CSV**: Recommendations table for reporting
- **Terraform**: Infrastructure as code for top recommendations
- **YAML**: Kubernetes manifests (via API)

```javascript
import { exportService } from './services/export';

// Export to CSV
exportService.downloadCSV(data, 'recommendations.csv');

// Export to Terraform
exportService.downloadJSON(terraformConfig, 'terraform.tf.json');

// Export to YAML
exportService.downloadYAML(k8sManifests, 'optimizations.yaml');
```

### Demo Mode

Toggle demo mode in Settings to use impressive sample data:

- 53 workloads across 3 clusters
- $4,560/month potential savings
- 36.6% average savings percentage
- 40+ recommendations

### Theme Support

Full dark/light theme support using Tailwind CSS:

```javascript
import { useTheme } from './hooks/useTheme';

const { theme, toggleTheme } = useTheme();
```

Theme preference is persisted to localStorage.

## API Integration

The dashboard connects to the optimizer API at `/api`:

### Endpoints Used

- `POST /analyze` - Analyze all workloads
- `GET /recommendations` - Get filtered recommendations
- `POST /optimize/{workloadId}` - Optimize specific workload
- `POST /apply/{recommendationId}` - Apply optimization
- `GET /savings/history` - Get historical savings
- `GET /export/csv` - Export as CSV
- `POST /export/terraform` - Export as Terraform
- `WS /ws` - WebSocket for real-time updates

### Example API Call

```javascript
import { api } from './services/api';

// Analyze workloads
const summary = await api.analyzeWorkloads({
  cluster_filter: ['aws-cluster'],
  min_confidence: 0.7
});

// Get recommendations
const recommendations = await api.getRecommendations({
  min_savings: 100,
  limit: 50
});
```

## Environment Variables

Configure the dashboard using environment variables:

```bash
VITE_API_URL=http://localhost:8000  # Optimizer API URL
VITE_WS_URL=ws://localhost:8000     # WebSocket URL
```

## Styling

The dashboard uses Tailwind CSS with a custom configuration:

- **Primary Color**: Blue (#3b82f6)
- **Success Color**: Green (#22c55e)
- **Warning Color**: Yellow (#f59e0b)
- **Danger Color**: Red (#ef4444)

Dark mode is supported via the `dark:` prefix.

## Performance

- **Code Splitting**: Automatic chunking by Vite
- **Lazy Loading**: Route-based code splitting
- **Optimized Builds**: Production builds are minified
- **Gzip Compression**: Enabled in nginx configuration
- **Asset Caching**: Static assets cached by nginx

## Deployment

### Production Build

```bash
npm run build
```

Output is generated in the `dist/` directory.

### Nginx Configuration

The dashboard uses nginx as a reverse proxy:

- Static files served from `/usr/share/nginx/html`
- API requests proxied to `http://optimizer-api:8000`
- WebSocket connections proxied to `ws://optimizer-api:8000/ws`
- Gzip compression enabled
- SPA routing support (`try_files` directive)

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Opera 76+

## Contributing

The dashboard follows standard React patterns:

1. Components in `src/components/`
2. Pages in `src/pages/`
3. Business logic in `src/services/`
4. Custom hooks in `src/hooks/`
5. Global state in `src/store/`

## Troubleshooting

### Dashboard not loading

Check that the optimizer API is running:

```bash
curl http://localhost:8000/health
```

### No data displayed

Enable demo mode in Settings to use sample data.

### WebSocket not connecting

Verify the WebSocket endpoint is accessible:

```bash
wscat -c ws://localhost:8000/ws
```

### Dark mode not persisting

Clear browser localStorage and try again.

## License

Part of the K8s Cost Optimizer platform.
