#!/bin/bash

# Record demo video with narration script

set -e

DEMO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VIDEO_DIR="$DEMO_DIR/reports/videos"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$VIDEO_DIR"

echo "K8s Cost Optimizer - Demo Recording Setup"
echo "=========================================="
echo ""

# Check for recording tools
if ! command -v asciinema &> /dev/null; then
    echo "⚠ asciinema not installed"
    echo "  Install: brew install asciinema"
    USE_ASCIINEMA=false
else
    USE_ASCIINEMA=true
fi

echo "Demo Narration Script"
echo "--------------------"
echo ""

cat << 'SCRIPT'
# K8s Cost Optimizer Demo - Narration Script

## Scene 1: Introduction (30 seconds)
"Welcome to the Kubernetes Cost Optimizer demo. Today I'll show you how we
helped a fast-growing startup reduce their AWS infrastructure costs by 43%,
saving over $29,000 per month."

## Scene 2: Initial Assessment (45 seconds)
"Let's start by looking at their current state. They're running 120 workloads
across production and staging environments, spending $68,450 per month."

[Show dashboard with current costs]

"As you can see, their compute costs are high, and resource utilization is
only 28%. This is a common pattern we see with rapid growth - teams
over-provision for safety."

## Scene 3: Analysis (60 seconds)
"Let's run our optimization analysis..."

[Run: demo/scripts/run-demo.sh]

"The analyzer examines 30 days of historical metrics, looking at CPU, memory,
network usage, and patterns. It uses machine learning to identify optimization
opportunities with high confidence."

"And we're done! In just 2 minutes, we've analyzed all 120 workloads and
generated 47 recommendations."

## Scene 4: Recommendations (90 seconds)
"Let's look at the top recommendations:"

[Show recommendations list]

"Number 1: Right-sizing. We found 45 web application pods requesting 2 CPUs
but using an average of only 500 millicores. By right-sizing these, we can
save $12,400 per month with 92% confidence."

"Number 2: Spot instances for batch jobs. These 35 batch processing jobs are
fault-tolerant and perfect for spot instances, saving $8,200 monthly."

"Number 3: Horizontal autoscaling. Many workloads have variable traffic
patterns. Enabling HPA will save $5,600 by scaling down during off-peak hours."

## Scene 5: Results (45 seconds)
"Here's the impact:"

[Show summary]

"- Current cost: $68,450/month
- After optimization: $38,920/month
- Savings: $29,530/month or $354,360 annually
- That's a 43% reduction!"

"And the best part? Implementation takes just 2-3 weeks with minimal risk.
We use gradual rollouts and continuous monitoring."

## Scene 6: Scenarios (30 seconds)
"We've included several pre-built scenarios:"

"- Startup optimization: 64% savings in 2 weeks
- Enterprise multi-cloud: $320K annual savings
- Emergency cost reduction: 50% cuts in 48 hours"

## Scene 7: Conclusion (20 seconds)
"The Kubernetes Cost Optimizer helps teams reduce cloud costs significantly
without impacting performance. Try it yourself with our demo environment."

"Thank you for watching!"

SCRIPT

echo ""
echo "Recording Options:"
echo "----------------- "
echo ""
echo "1. Terminal recording with asciinema:"
if [ "$USE_ASCIINEMA" = true ]; then
    echo "   asciinema rec $VIDEO_DIR/demo_$TIMESTAMP.cast"
    echo "   (Press Ctrl+D when done)"
else
    echo "   [Not available - install asciinema]"
fi
echo ""
echo "2. Screen recording with QuickTime (macOS):"
echo "   - Open QuickTime Player"
echo "   - File → New Screen Recording"
echo "   - Select browser window with dashboard"
echo "   - Save to: $VIDEO_DIR/"
echo ""
echo "3. Browser-based recording:"
echo "   - Open dashboard at http://localhost:3000"
echo "   - Use Loom, OBS Studio, or browser extension"
echo ""
echo "Demo Duration: ~5 minutes"
echo "Recommended Resolution: 1920x1080"
echo ""
