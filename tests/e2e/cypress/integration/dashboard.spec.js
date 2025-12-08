/**
 * End-to-end tests for Cost Optimizer Dashboard
 *
 * Tests user workflows including:
 * - Dashboard navigation
 * - Viewing recommendations
 * - Applying optimizations
 * - Cost tracking
 */

describe('Dashboard Homepage', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('should load dashboard successfully', () => {
    cy.contains('Cost Optimizer Dashboard')
    cy.get('[data-testid="total-savings"]').should('be.visible')
    cy.get('[data-testid="cluster-selector"]').should('be.visible')
  })

  it('should display cost summary cards', () => {
    cy.get('[data-testid="current-cost-card"]').should('contain', '$')
    cy.get('[data-testid="projected-savings-card"]').should('contain', '$')
    cy.get('[data-testid="optimization-score-card"]').should('be.visible')
  })

  it('should show cost trend chart', () => {
    cy.get('[data-testid="cost-trend-chart"]').should('be.visible')
    cy.get('[data-testid="chart-legend"]').should('contain', 'Compute')
    cy.get('[data-testid="chart-legend"]').should('contain', 'Storage')
  })

  it('should allow changing time range', () => {
    cy.get('[data-testid="timerange-selector"]').click()
    cy.contains('Last 30 days').click()

    cy.wait(500) // Wait for chart update
    cy.get('[data-testid="cost-trend-chart"]').should('be.visible')
  })
})

describe('Recommendations Page', () => {
  beforeEach(() => {
    cy.visit('/recommendations')
  })

  it('should list all recommendations', () => {
    cy.get('[data-testid="recommendation-card"]').should('have.length.at.least', 1)
  })

  it('should filter recommendations by type', () => {
    cy.get('[data-testid="filter-type"]').click()
    cy.contains('Right-sizing').click()

    cy.get('[data-testid="recommendation-card"]').each($card => {
      cy.wrap($card).should('contain', 'Right-sizing')
    })
  })

  it('should sort recommendations by savings', () => {
    cy.get('[data-testid="sort-by"]').select('Highest Savings')

    let previousSavings = Infinity
    cy.get('[data-testid="recommendation-savings"]').each($el => {
      const savings = parseFloat($el.text().replace(/[^0-9.]/g, ''))
      expect(savings).to.be.at.most(previousSavings)
      previousSavings = savings
    })
  })

  it('should show recommendation details', () => {
    cy.get('[data-testid="recommendation-card"]').first().click()

    cy.get('[data-testid="recommendation-details"]').should('be.visible')
    cy.get('[data-testid="confidence-score"]').should('be.visible')
    cy.get('[data-testid="estimated-savings"]').should('contain', '$')
    cy.get('[data-testid="impact-analysis"]').should('be.visible')
  })

  it('should preview changes before applying', () => {
    cy.get('[data-testid="recommendation-card"]').first().click()
    cy.get('[data-testid="preview-button"]').click()

    cy.get('[data-testid="diff-view"]').should('be.visible')
    cy.get('[data-testid="current-config"]').should('be.visible')
    cy.get('[data-testid="recommended-config"]').should('be.visible')
  })
})

describe('Apply Recommendation Workflow', () => {
  beforeEach(() => {
    cy.visit('/recommendations')
    cy.get('[data-testid="recommendation-card"]').first().click()
  })

  it('should apply recommendation in dry-run mode', () => {
    cy.get('[data-testid="apply-button"]').click()
    cy.get('[data-testid="dry-run-checkbox"]').check()
    cy.get('[data-testid="confirm-apply"]').click()

    cy.contains('Dry-run completed').should('be.visible')
    cy.get('[data-testid="dry-run-results"]').should('be.visible')
  })

  it('should show confirmation dialog for live apply', () => {
    cy.get('[data-testid="apply-button"]').click()
    cy.get('[data-testid="dry-run-checkbox"]').uncheck()
    cy.get('[data-testid="confirm-apply"]').click()

    cy.get('[data-testid="confirmation-dialog"]').should('be.visible')
    cy.contains('Are you sure').should('be.visible')
  })

  it('should track application progress', () => {
    cy.intercept('POST', '/api/v1/recommendations/*/apply').as('applyRec')

    cy.get('[data-testid="apply-button"]').click()
    cy.get('[data-testid="dry-run-checkbox"]').check()
    cy.get('[data-testid="confirm-apply"]').click()

    cy.wait('@applyRec')
    cy.get('[data-testid="progress-indicator"]').should('be.visible')
  })
})

describe('Cost Analysis Page', () => {
  beforeEach(() => {
    cy.visit('/costs')
  })

  it('should display cost breakdown by service', () => {
    cy.get('[data-testid="cost-breakdown-chart"]').should('be.visible')
    cy.contains('Compute').should('be.visible')
    cy.contains('Storage').should('be.visible')
    cy.contains('Network').should('be.visible')
  })

  it('should show cost by namespace', () => {
    cy.get('[data-testid="namespace-costs"]').should('be.visible')
    cy.get('[data-testid="namespace-row"]').should('have.length.at.least', 1)
  })

  it('should export cost report', () => {
    cy.get('[data-testid="export-button"]').click()
    cy.contains('Export as CSV').click()

    // Verify download initiated
    cy.readFile('cypress/downloads/cost-report.csv').should('exist')
  })

  it('should filter costs by date range', () => {
    cy.get('[data-testid="start-date"]').type('2024-01-01')
    cy.get('[data-testid="end-date"]').type('2024-01-31')
    cy.get('[data-testid="apply-filter"]').click()

    cy.get('[data-testid="cost-breakdown-chart"]').should('be.visible')
  })
})

describe('Cluster Management', () => {
  beforeEach(() => {
    cy.visit('/clusters')
  })

  it('should list all clusters', () => {
    cy.get('[data-testid="cluster-card"]').should('have.length.at.least', 1)
  })

  it('should show cluster details', () => {
    cy.get('[data-testid="cluster-card"]').first().click()

    cy.get('[data-testid="cluster-name"]').should('be.visible')
    cy.get('[data-testid="cluster-status"]').should('be.visible')
    cy.get('[data-testid="node-count"]').should('be.visible')
    cy.get('[data-testid="workload-count"]').should('be.visible')
  })

  it('should trigger new analysis', () => {
    cy.get('[data-testid="cluster-card"]').first().click()
    cy.get('[data-testid="start-analysis-button"]').click()

    cy.get('[data-testid="analysis-config"]').should('be.visible')
    cy.get('[data-testid="lookback-days"]').select('7')
    cy.get('[data-testid="start-analysis"]').click()

    cy.contains('Analysis started').should('be.visible')
  })
})

describe('Mobile Responsiveness', () => {
  const sizes = ['iphone-6', 'ipad-2', [1024, 768]]

  sizes.forEach(size => {
    it(`should be responsive on ${size}`, () => {
      if (Cypress._.isArray(size)) {
        cy.viewport(size[0], size[1])
      } else {
        cy.viewport(size)
      }

      cy.visit('/')
      cy.get('[data-testid="mobile-menu"]').should('be.visible')
      cy.get('[data-testid="total-savings"]').should('be.visible')
    })
  })
})

describe('Dark Mode', () => {
  it('should toggle dark mode', () => {
    cy.visit('/')

    cy.get('[data-testid="theme-toggle"]').click()
    cy.get('body').should('have.class', 'dark-mode')

    cy.get('[data-testid="theme-toggle"]').click()
    cy.get('body').should('not.have.class', 'dark-mode')
  })

  it('should persist theme preference', () => {
    cy.visit('/')
    cy.get('[data-testid="theme-toggle"]').click()

    cy.reload()
    cy.get('body').should('have.class', 'dark-mode')
  })
})

describe('Search and Filters', () => {
  beforeEach(() => {
    cy.visit('/recommendations')
  })

  it('should search recommendations by workload name', () => {
    cy.get('[data-testid="search-input"]').type('api-service')

    cy.get('[data-testid="recommendation-card"]').each($card => {
      cy.wrap($card).should('contain', 'api-service')
    })
  })

  it('should filter by confidence level', () => {
    cy.get('[data-testid="confidence-filter"]').click()
    cy.contains('High (>0.8)').click()

    cy.get('[data-testid="confidence-badge"]').each($badge => {
      const confidence = parseFloat($badge.text())
      expect(confidence).to.be.greaterThan(0.8)
    })
  })

  it('should combine multiple filters', () => {
    cy.get('[data-testid="filter-type"]').click()
    cy.contains('Right-sizing').click()

    cy.get('[data-testid="confidence-filter"]').click()
    cy.contains('High').click()

    cy.get('[data-testid="recommendation-card"]').should('have.length.at.least', 1)
  })
})

describe('Performance', () => {
  it('should load dashboard within 3 seconds', () => {
    const start = Date.now()

    cy.visit('/')
    cy.get('[data-testid="total-savings"]').should('be.visible')

    const loadTime = Date.now() - start
    expect(loadTime).to.be.lessThan(3000)
  })

  it('should handle large recommendation lists', () => {
    cy.intercept('GET', '/api/v1/recommendations', {
      fixture: 'large-recommendations-list.json'
    }).as('getRecommendations')

    cy.visit('/recommendations')
    cy.wait('@getRecommendations')

    // Should use virtualization for large lists
    cy.get('[data-testid="recommendation-card"]').should('be.visible')
    cy.scrollTo('bottom')
    cy.get('[data-testid="recommendation-card"]').should('be.visible')
  })
})

describe('Error Handling', () => {
  it('should handle API errors gracefully', () => {
    cy.intercept('GET', '/api/v1/recommendations', {
      statusCode: 500,
      body: { error: 'Internal server error' }
    }).as('getRecommendations')

    cy.visit('/recommendations')
    cy.wait('@getRecommendations')

    cy.contains('Error loading recommendations').should('be.visible')
    cy.get('[data-testid="retry-button"]').should('be.visible')
  })

  it('should show loading states', () => {
    cy.intercept('GET', '/api/v1/recommendations', (req) => {
      req.reply((res) => {
        res.delay = 2000
        res.send({ recommendations: [] })
      })
    }).as('getRecommendations')

    cy.visit('/recommendations')
    cy.get('[data-testid="loading-spinner"]').should('be.visible')
    cy.wait('@getRecommendations')
    cy.get('[data-testid="loading-spinner"]').should('not.exist')
  })
})
