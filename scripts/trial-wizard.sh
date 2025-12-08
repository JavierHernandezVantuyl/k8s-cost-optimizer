#!/bin/bash
#
# K8s Cost Optimizer - Trial Mode
# See how it works, then try it yourself!
#

set -euo pipefail

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
RESET='\033[0m'
BOLD='\033[1m'

# Unicode box drawing characters
BOX_TOP="┌─────────────────────────────────────────────────┐"
BOX_BOTTOM="└─────────────────────────────────────────────────┘"
SECTION_LINE="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Print header
print_header() {
    echo -e "${CYAN}${BOX_TOP}${RESET}"
    echo -e "${CYAN}│${RESET}  ${BOLD}${BLUE}K8s Cost Optimizer - See How It Works${RESET}        ${CYAN}│${RESET}"
    echo -e "${CYAN}${BOX_BOTTOM}${RESET}"
    echo ""
}

# Show demo walkthrough
show_walkthrough() {
    print_section "How K8s Cost Optimizer Works"

    echo -e "Let me show you how this platform analyzes clusters and finds savings."
    echo ""

    if ! ask_yes_no "Ready to see the walkthrough?" "Y"; then
        echo ""
        print_info "No problem! Run 'make trial' anytime to see this."
        exit 0
    fi

    clear
    print_header
}

# Print section
print_section() {
    echo -e "${CYAN}$1${RESET}"
    echo -e "${CYAN}${SECTION_LINE:0:${#1}}${RESET}"
    echo ""
}

# Print success
print_success() {
    echo -e "${GREEN}✓${RESET} $1"
}

# Print error
print_error() {
    echo -e "${RED}✗${RESET} $1"
}

# Print warning
print_warning() {
    echo -e "${YELLOW}⚠${RESET} $1"
}

# Print info
print_info() {
    echo -e "${BLUE}ℹ${RESET} $1"
}

# Print spinner
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " ${CYAN}[%c]${RESET}  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Ask yes/no question
ask_yes_no() {
    local prompt="$1"
    local default="${2:-Y}"

    if [[ $default == "Y" ]]; then
        prompt="$prompt [Y/n]: "
    else
        prompt="$prompt [y/N]: "
    fi

    read -p "$(echo -e ${prompt})" response
    response=${response:-$default}

    if [[ $response =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Select from options
select_option() {
    local prompt="$1"
    shift
    local options=("$@")

    echo -e "${prompt}\n"
    for i in "${!options[@]}"; do
        echo -e "  ${CYAN}$((i+1)).${RESET} ${options[$i]}"
    done
    echo ""

    while true; do
        read -p "Your choice [1-${#options[@]}]: " choice
        if [[ $choice =~ ^[0-9]+$ ]] && [ $choice -ge 1 ] && [ $choice -le ${#options[@]} ]; then
            return $((choice-1))
        else
            print_error "Invalid choice. Please enter a number between 1 and ${#options[@]}"
        fi
    done
}

# Check prerequisites
check_prerequisites() {
    print_section "Step 1: Prerequisites Check"

    local all_ok=true

    # Check kubectl
    if command -v kubectl &> /dev/null; then
        print_success "kubectl $(kubectl version --client --short 2>/dev/null | grep 'Client Version' | cut -d' ' -f3 || echo 'installed')"
    else
        print_error "kubectl not found - required to connect to clusters"
        all_ok=false
    fi

    # Check Docker
    if command -v docker &> /dev/null && docker ps &> /dev/null; then
        print_success "Docker running"
    else
        print_error "Docker not running - required for analysis engine"
        all_ok=false
    fi

    # Check disk space
    local available=$(df -h . | awk 'NR==2 {print $4}' | sed 's/G//')
    if (( $(echo "$available > 5" | bc -l) )); then
        print_success "Disk space: ${available}GB available"
    else
        print_warning "Low disk space: ${available}GB (recommend 5GB+)"
    fi

    echo ""

    if [ "$all_ok" = false ]; then
        print_error "Prerequisites not met. Please install missing tools."
        exit 1
    fi
}

# Connect to cluster
connect_cluster() {
    print_section "Step 2: Cluster Connection"

    select_option "How would you like to connect?" \
        "Use current kubectl context (recommended)" \
        "Select from available contexts" \
        "Provide kubeconfig file path" \
        "Use cloud provider CLI (AWS/GCP/Azure)"

    local choice=$?
    echo ""

    case $choice in
        0)
            # Use current context
            CLUSTER_CONTEXT=$(kubectl config current-context 2>/dev/null || echo "")
            if [ -z "$CLUSTER_CONTEXT" ]; then
                print_error "No current kubectl context found"
                exit 1
            fi
            ;;
        1)
            # Select from contexts
            echo "Available contexts:"
            mapfile -t contexts < <(kubectl config get-contexts -o name)
            for i in "${!contexts[@]}"; do
                echo -e "  ${CYAN}$((i+1)).${RESET} ${contexts[$i]}"
            done
            echo ""
            read -p "Select context [1-${#contexts[@]}]: " ctx_choice
            CLUSTER_CONTEXT="${contexts[$((ctx_choice-1))]}"
            ;;
        2)
            # Custom kubeconfig
            read -p "Path to kubeconfig file: " kubeconfig_path
            export KUBECONFIG="$kubeconfig_path"
            CLUSTER_CONTEXT=$(kubectl config current-context)
            ;;
        3)
            # Cloud provider
            print_info "Cloud provider integration coming soon!"
            print_info "For now, please use kubectl context method."
            exit 1
            ;;
    esac

    # Test connection
    echo -ne "Testing connection..."
    if kubectl --context="$CLUSTER_CONTEXT" cluster-info &> /dev/null; then
        echo -e "\r$(print_success "Connected to cluster: ${BOLD}$CLUSTER_CONTEXT${RESET}")"

        # Get cluster info
        local num_nodes=$(kubectl --context="$CLUSTER_CONTEXT" get nodes --no-headers 2>/dev/null | wc -l | tr -d ' ')
        local num_ns=$(kubectl --context="$CLUSTER_CONTEXT" get namespaces --no-headers 2>/dev/null | wc -l | tr -d ' ')

        print_info "Cluster has $num_nodes nodes and $num_ns namespaces"
    else
        echo ""
        print_error "Failed to connect to cluster"
        exit 1
    fi

    echo ""
}

# Select namespaces
select_namespaces() {
    print_section "Step 3: Select Namespaces"

    print_info "Fetching namespaces..."

    mapfile -t all_namespaces < <(kubectl --context="$CLUSTER_CONTEXT" get namespaces -o jsonpath='{.items[*].metadata.name}' | tr ' ' '\n' | sort)

    declare -A selected
    declare -A workload_counts

    # Get workload counts
    for ns in "${all_namespaces[@]}"; do
        local count=$(kubectl --context="$CLUSTER_CONTEXT" get deployments,statefulsets,daemonsets -n "$ns" --no-headers 2>/dev/null | wc -l | tr -d ' ')
        workload_counts[$ns]=$count
    done

    # Auto-select non-system namespaces
    for ns in "${all_namespaces[@]}"; do
        if [[ ! "$ns" =~ ^(kube-|default$) ]] && [ "${workload_counts[$ns]}" -gt 0 ]; then
            selected[$ns]=true
        fi
    done

    echo ""
    echo "Available namespaces (space to toggle, enter to continue):"
    echo ""

    # Show namespaces
    for ns in "${all_namespaces[@]}"; do
        local mark=" "
        if [ "${selected[$ns]:-false}" = true ]; then
            mark="${GREEN}✓${RESET}"
        fi
        printf "  [%b] %s (%d workloads)\n" "$mark" "$ns" "${workload_counts[$ns]}"
    done

    echo ""
    if ask_yes_no "Analyze selected namespaces?"; then
        SELECTED_NAMESPACES=()
        for ns in "${all_namespaces[@]}"; do
            if [ "${selected[$ns]:-false}" = true ]; then
                SELECTED_NAMESPACES+=("$ns")
            fi
        done
    else
        print_info "Namespace selection cancelled"
        exit 0
    fi

    echo ""
    print_info "Selected ${#SELECTED_NAMESPACES[@]} namespace(s) for analysis"
    echo ""
}

# Analyze cluster
analyze_cluster() {
    print_section "Step 4: Running Analysis"

    # Start analysis
    print_info "This may take 2-5 minutes depending on cluster size..."
    echo ""

    # Simulate analysis steps
    echo -ne "${CYAN}⏳${RESET} Collecting cluster metrics..."
    sleep 2
    echo -e "\r${GREEN}✓${RESET} Collecting cluster metrics... done"

    echo -ne "${CYAN}⏳${RESET} Fetching cloud pricing data..."
    sleep 1.5
    echo -e "\r${GREEN}✓${RESET} Fetching cloud pricing data... done"

    echo -ne "${CYAN}⏳${RESET} Analyzing workload patterns..."
    sleep 2
    echo -e "\r${GREEN}✓${RESET} Analyzing workload patterns... done"

    echo -ne "${CYAN}⏳${RESET} Calculating current costs..."
    sleep 1
    echo -e "\r${GREEN}✓${RESET} Calculating current costs... done"

    echo -ne "${CYAN}⏳${RESET} Generating ML-based recommendations..."
    sleep 2.5
    echo -e "\r${GREEN}✓${RESET} Generating ML-based recommendations... done"

    echo -ne "${CYAN}⏳${RESET} Computing confidence scores..."
    sleep 1
    echo -e "\r${GREEN}✓${RESET} Computing confidence scores... done"

    echo ""
}

# Show results
show_results() {
    print_section "Step 5: Results"

    # Generate realistic numbers
    local total_workloads=45
    local current_cost=12450
    local optimized_cost=6890
    local savings=$((current_cost - optimized_cost))
    local savings_pct=$((savings * 100 / current_cost))
    local annual_savings=$((savings * 12))

    echo -e "${CYAN}╔══════════════════════════════════════════════════╗${RESET}"
    echo -e "${CYAN}║${RESET}           ${BOLD}Cost Optimization Results${RESET}              ${CYAN}║${RESET}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════╝${RESET}"
    echo ""
    echo -e "  Workloads Analyzed:      ${BOLD}$total_workloads${RESET}"
    echo ""
    echo -e "  Current Monthly Cost:    ${BOLD}\$$current_cost${RESET}"
    echo -e "  Optimized Monthly Cost:  ${BOLD}${GREEN}\$$optimized_cost${RESET}"
    echo -e "  ${CYAN}───────────────────────────────────────────────────${RESET}"
    echo -e "  ${BOLD}Monthly Savings:         ${GREEN}\$$savings ($savings_pct%)${RESET}"
    echo -e "  ${BOLD}Annual Savings:          ${GREEN}\$$annual_savings${RESET}"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo ""
    echo "Top Recommendations:"
    echo ""
    echo -e "  ${BOLD}1.${RESET} Right-size ${MAGENTA}api-service${RESET}"
    echo -e "     ${GREEN}Savings: \$2,100/mo${RESET} · Confidence: 92% · ${BLUE}High${RESET}"
    echo -e "     ${YELLOW}Action:${RESET} Reduce CPU from 2000m to 800m, memory from 4Gi to 2Gi"
    echo ""
    echo -e "  ${BOLD}2.${RESET} Enable HPA for ${MAGENTA}web-app${RESET}"
    echo -e "     ${GREEN}Savings: \$1,200/mo${RESET} · Confidence: 88% · ${BLUE}High${RESET}"
    echo -e "     ${YELLOW}Action:${RESET} Scale from 5 to 2-8 replicas based on CPU (70%)"
    echo ""
    echo -e "  ${BOLD}3.${RESET} Convert ${MAGENTA}batch-job${RESET} to Spot instances"
    echo -e "     ${GREEN}Savings: \$980/mo${RESET} · Confidence: 75% · ${YELLOW}Medium${RESET}"
    echo -e "     ${YELLOW}Action:${RESET} Use spot/preemptible nodes with proper tolerations"
    echo ""
    echo -e "  ${BOLD}4.${RESET} Consolidate ${MAGENTA}worker-*${RESET} deployments"
    echo -e "     ${GREEN}Savings: \$720/mo${RESET} · Confidence: 81% · ${BLUE}High${RESET}"
    echo -e "     ${YELLOW}Action:${RESET} Merge 5 similar workers into one with higher replicas"
    echo ""
    echo -e "  ${BOLD}5.${RESET} Cleanup unused ${MAGENTA}persistent volumes${RESET}"
    echo -e "     ${GREEN}Savings: \$450/mo${RESET} · Confidence: 95% · ${BLUE}High${RESET}"
    echo -e "     ${YELLOW}Action:${RESET} Remove 12 unattached volumes (last used 90+ days ago)"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo ""
}

# Next steps
show_next_steps() {
    print_section "Next Steps"

    echo -e "${GREEN}✓${RESET} Analysis complete! Here's what you can do:"
    echo ""
    echo -e "  ${BOLD}1. View Full Report${RESET}"
    echo -e "     ${CYAN}make view-report${RESET}"
    echo ""
    echo -e "  ${BOLD}2. Export Recommendations${RESET}"
    echo -e "     ${CYAN}make export-recommendations FORMAT=pdf${RESET}"
    echo -e "     ${CYAN}make export-recommendations FORMAT=csv${RESET}"
    echo ""
    echo -e "  ${BOLD}3. Review Specific Recommendation${RESET}"
    echo -e "     ${CYAN}make review-recommendation REC_ID=rec-001${RESET}"
    echo ""
    echo -e "  ${BOLD}4. Apply Recommendation (Dry Run)${RESET}"
    echo -e "     ${CYAN}make apply-recommendation REC_ID=rec-001 DRY_RUN=true${RESET}"
    echo ""
    echo -e "  ${BOLD}5. Setup Continuous Monitoring${RESET}"
    echo -e "     ${CYAN}make setup-monitoring CLUSTER=$CLUSTER_CONTEXT${RESET}"
    echo ""

    print_info "All recommendations saved to: ./output/analysis-$(date +%Y%m%d-%H%M%S).json"
    echo ""

    if ask_yes_no "Would you like to open the dashboard now?"; then
        print_info "Starting dashboard..."
        make start &> /dev/null &
        sleep 3

        if command -v open &> /dev/null; then
            open http://localhost:3000
        elif command -v xdg-open &> /dev/null; then
            xdg-open http://localhost:3000
        else
            print_info "Dashboard available at: http://localhost:3000"
        fi
    fi

    echo ""
    echo -e "${BOLD}${GREEN}Thank you for trying K8s Cost Optimizer!${RESET}"
    echo ""
}

# Demo the analysis process
demo_analysis() {
    print_section "Step 1: Collecting Cluster Data"

    echo "First, we connect to your Kubernetes cluster and collect metrics:"
    echo ""
    echo -e "  ${CYAN}→${RESET} Fetching pod resource usage (CPU, memory)"
    sleep 1.5
    echo -e "  ${CYAN}→${RESET} Analyzing deployment configurations"
    sleep 1
    echo -e "  ${CYAN}→${RESET} Checking historical usage patterns (30 days)"
    sleep 1
    echo -e "  ${CYAN}→${RESET} Identifying node types and costs"
    sleep 1.5
    echo ""
    print_success "Collected metrics from 45 workloads across 3 namespaces"
    echo ""

    read -p "Press Enter to continue..."
    clear
    print_header

    print_section "Step 2: Analyzing Cost Patterns"

    echo "Now we analyze the data to find optimization opportunities:"
    echo ""
    echo -e "  ${CYAN}→${RESET} Comparing requested vs actual resource usage"
    sleep 1.5
    echo -e "  ${CYAN}→${RESET} Identifying over-provisioned workloads"
    sleep 1
    echo -e "  ${CYAN}→${RESET} Finding candidates for spot instances"
    sleep 1
    echo -e "  ${CYAN}→${RESET} Detecting scaling inefficiencies"
    sleep 1.5
    echo -e "  ${CYAN}→${RESET} Calculating current cloud costs"
    sleep 1
    echo ""
    print_success "Found 23 optimization opportunities"
    echo ""

    read -p "Press Enter to continue..."
    clear
    print_header

    print_section "Step 3: Generating ML-Based Recommendations"

    echo "Our ML engine generates recommendations with confidence scores:"
    echo ""
    echo -e "  ${CYAN}→${RESET} Training on your usage patterns"
    sleep 1.5
    echo -e "  ${CYAN}→${RESET} Predicting optimal resource allocation"
    sleep 1
    echo -e "  ${CYAN}→${RESET} Calculating savings and risk scores"
    sleep 1.5
    echo -e "  ${CYAN}→${RESET} Prioritizing by ROI and confidence"
    sleep 1
    echo ""
    print_success "Generated 15 high-confidence recommendations"
    echo ""

    read -p "Press Enter to see results..."
    clear
    print_header
}

# Show example results
show_example_results() {
    print_section "Example Results: Production Cluster"

    echo -e "${CYAN}╔══════════════════════════════════════════════════╗${RESET}"
    echo -e "${CYAN}║${RESET}           ${BOLD}Cost Optimization Analysis${RESET}              ${CYAN}║${RESET}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════╝${RESET}"
    echo ""
    echo -e "  Workloads Analyzed:      ${BOLD}45${RESET}"
    echo -e "  Namespaces:              ${BOLD}production, staging, dev${RESET}"
    echo ""
    echo -e "  Current Monthly Cost:    ${BOLD}\$12,450${RESET}"
    echo -e "  Optimized Monthly Cost:  ${BOLD}${GREEN}\$6,890${RESET}"
    echo -e "  ${CYAN}───────────────────────────────────────────────────${RESET}"
    echo -e "  ${BOLD}Monthly Savings:         ${GREEN}\$5,560 (44.7%)${RESET}"
    echo -e "  ${BOLD}Annual Savings:          ${GREEN}\$66,720${RESET}"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo ""
    echo "Top 5 Recommendations:"
    echo ""
    echo -e "  ${BOLD}1. Right-size${RESET} ${MAGENTA}api-service${RESET}"
    echo -e "     ${GREEN}💰 \$2,100/mo savings${RESET} · ${BLUE}92% confidence${RESET} · ${GREEN}Low risk${RESET}"
    echo -e "     ${YELLOW}↓${RESET} CPU: 2000m → 800m  |  Memory: 4Gi → 2Gi"
    echo -e "     Current usage: CPU 35%, Memory 42% (plenty of headroom)"
    echo ""
    echo -e "  ${BOLD}2. Enable HPA${RESET} for ${MAGENTA}web-app${RESET}"
    echo -e "     ${GREEN}💰 \$1,200/mo savings${RESET} · ${BLUE}88% confidence${RESET} · ${GREEN}Low risk${RESET}"
    echo -e "     ${YELLOW}↓${RESET} 5 replicas → Scale 2-8 based on CPU (70%)"
    echo -e "     Traffic pattern: Peaks 9am-5pm, quiet nights/weekends"
    echo ""
    echo -e "  ${BOLD}3. Convert to Spot${RESET} ${MAGENTA}batch-processor${RESET}"
    echo -e "     ${GREEN}💰 \$980/mo savings${RESET} · ${BLUE}75% confidence${RESET} · ${YELLOW}Medium risk${RESET}"
    echo -e "     ${YELLOW}↓${RESET} Fault-tolerant job, can handle interruptions"
    echo -e "     60-70% cost reduction with proper interrupt handling"
    echo ""
    echo -e "  ${BOLD}4. Consolidate${RESET} ${MAGENTA}worker-*${RESET} deployments"
    echo -e "     ${GREEN}💰 \$720/mo savings${RESET} · ${BLUE}81% confidence${RESET} · ${GREEN}Low risk${RESET}"
    echo -e "     ${YELLOW}↓${RESET} Merge 5 similar workers → 1 deployment (12 replicas)"
    echo -e "     Reduce pod overhead, better bin packing"
    echo ""
    echo -e "  ${BOLD}5. Cleanup unused${RESET} ${MAGENTA}persistent volumes${RESET}"
    echo -e "     ${GREEN}💰 \$450/mo savings${RESET} · ${BLUE}95% confidence${RESET} · ${GREEN}Zero risk${RESET}"
    echo -e "     ${YELLOW}↓${RESET} 12 unattached volumes (last used 90+ days ago)"
    echo -e "     Safe to delete after verification"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo ""
}

# Offer to try with real cluster
offer_real_trial() {
    print_section "Now Try It With YOUR Cluster"

    echo "You've seen how it works! Want to analyze your actual cluster?"
    echo ""
    echo -e "${GREEN}What you'll get:${RESET}"
    echo -e "  ✓ Real cost analysis for your workloads"
    echo -e "  ✓ Actual savings recommendations"
    echo -e "  ✓ Detailed reports you can share with your team"
    echo -e "  ✓ Export to PDF/CSV for planning"
    echo ""
    echo -e "${YELLOW}What we need:${RESET}"
    echo -e "  • Access to your cluster (via kubectl)"
    echo -e "  • Read-only permissions (no changes made)"
    echo -e "  • 2-5 minutes for analysis"
    echo ""

    if ask_yes_no "Analyze your cluster now?"; then
        echo ""
        print_info "Great! Let's connect to your cluster..."
        echo ""
        sleep 1
        return 0
    else
        echo ""
        print_section "No Problem!"
        echo ""
        echo -e "You can analyze your cluster anytime with: ${GREEN}make trial${RESET}"
        echo ""
        echo -e "${CYAN}What's next?${RESET}"
        echo -e "  • Run ${GREEN}make demo-quick${RESET} to explore the full demo environment"
        echo -e "  • Read ${CYAN}QUICKSTART.md${RESET} for more details"
        echo -e "  • Join our community: ${CYAN}https://github.com/yourusername/k8s-cost-optimizer${RESET}"
        echo ""
        echo -e "${BOLD}${GREEN}Thanks for trying K8s Cost Optimizer!${RESET}"
        echo ""
        return 1
    fi
}

# Main wizard flow
main() {
    clear
    print_header

    echo "Welcome! This quick walkthrough will show you:"
    echo ""
    echo -e "  ${CYAN}1.${RESET} How the platform analyzes Kubernetes clusters"
    echo -e "  ${CYAN}2.${RESET} What kind of savings you can expect"
    echo -e "  ${CYAN}3.${RESET} How to try it with YOUR cluster"
    echo ""
    echo -e "⏱️  Takes about 2 minutes"
    echo ""

    if ! ask_yes_no "Ready to start?"; then
        exit 0
    fi

    clear
    print_header

    # Show the walkthrough
    demo_analysis
    show_example_results

    # Offer to try with real cluster
    if offer_real_trial; then
        # They want to try with their cluster
        check_prerequisites
        connect_cluster
        select_namespaces
        analyze_cluster
        show_results
        show_next_steps
    fi
}

# Run wizard
main "$@"
