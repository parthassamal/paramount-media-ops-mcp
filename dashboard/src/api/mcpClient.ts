/**
 * MCP Server API Client
 * 
 * Connects the React dashboard to the Python MCP server
 * for live Pareto analysis and operational data.
 */

// Type fallback for environments where Vite types aren't picked up by tooling
export {};
declare global {
  interface ImportMetaEnv {
    VITE_MCP_URL?: string;
  }
  interface ImportMeta {
    readonly env: ImportMetaEnv;
  }
}

const MCP_BASE_URL = import.meta.env.VITE_MCP_URL || 'http://localhost:8000';

export interface MCPResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
}

export interface ChurnCohort {
  cohort_id: string;
  name: string;
  size: number;
  churn_risk_score: number;
  projected_churners_30d: number;
  financial_impact_30d: number;
  primary_driver: string;
}

export interface ParetoAnalysis {
  top_20_percent_contribution: number;
  is_pareto_valid: boolean;
  validation_message: string;
  total_impact: number;
}

export interface RetentionMetrics {
  total_subscribers: number;
  total_at_risk_30d: number;
  churn_rate_30d: number;
  annual_projected_impact: number;
}

export interface ChurnSignalsResponse {
  cohorts: ChurnCohort[];
  retention_metrics: RetentionMetrics;
  pareto_analysis?: ParetoAnalysis;
}

export interface ProductionIssue {
  issue_id: string;
  title: string;
  status: string;
  severity: string;
  priority?: string;
  show?: string;
  cost_overrun?: number;
  delay_days?: number;
  revenue_at_risk?: number;
  days_open?: number;
  jira_url?: string;
}

export interface ProductionIssuesResponse {
  issues: ProductionIssue[];
  cost_summary?: Record<string, unknown>;
  pareto_analysis?: Record<string, unknown>;
}

/**
 * Query a resource from the MCP server
 */
export async function queryResource<T>(
  resourceName: string,
  params: Record<string, unknown> = {}
): Promise<MCPResponse<T>> {
  try {
    const response = await fetch(`${MCP_BASE_URL}/resources/${resourceName}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`Error querying resource ${resourceName}:`, error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString(),
    };
  }
}

/**
 * Execute a tool on the MCP server
 */
export async function executeTool<T>(
  toolName: string,
  params: Record<string, unknown> = {}
): Promise<MCPResponse<T>> {
  try {
    const response = await fetch(`${MCP_BASE_URL}/tools/${toolName}/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`Error executing tool ${toolName}:`, error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString(),
    };
  }
}

/**
 * Get churn signals with Pareto analysis
 */
export async function getChurnSignals(
  riskThreshold: number = 0.5
): Promise<ChurnSignalsResponse | null> {
  const response = await queryResource<{ result: ChurnSignalsResponse }>(
    'churn_signals',
    { risk_threshold: riskThreshold }
  );

  if (response.success && response.data) {
    return response.data.result;
  }

  return null;
}

/**
 * Get production issues (Jira-backed when enabled)
 */
export async function getProductionIssues(params: {
  severity?: string;
  status?: string[];
  limit?: number;
  include_pareto?: boolean;
} = {}): Promise<ProductionIssuesResponse | null> {
  const response = await queryResource<{ result: ProductionIssuesResponse }>(
    'production_issues',
    params
  );

  if (response.success && response.data) {
    return response.data.result;
  }

  return null;
}

/**
 * Get health status of MCP server
 */
export async function getHealthStatus(): Promise<{
  status: string;
  resources_available: number;
  tools_available: number;
} | null> {
  try {
    const response = await fetch(`${MCP_BASE_URL}/health`);
    const data = await response.json();
    
    if (data.success) {
      return data.data;
    }
  } catch (error) {
    console.error('Error checking health:', error);
  }
  
  return null;
}

/**
 * Check if MCP server is running
 */
export async function isMCPServerRunning(): Promise<boolean> {
  try {
    const health = await getHealthStatus();
    return health?.status === 'healthy';
  } catch {
    return false;
  }
}


