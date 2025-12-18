/**
 * Unit tests for ProductionTracking component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { ProductionTracking } from '../ProductionTracking';
import { mcpClient } from '../../../api/mcpClient';

// Mock the MCP client
vi.mock('../../../api/mcpClient', () => ({
  mcpClient: {
    getProductionIssues: vi.fn()
  }
}));

describe('ProductionTracking', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render loading state initially', () => {
    (mcpClient.getProductionIssues as any).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<ProductionTracking />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('should render production issues when data is loaded', async () => {
    const mockIssues = [
      {
        id: 'PROD-001',
        key: 'PROD-001',
        summary: 'Color grading delays',
        status: 'In Progress',
        severity: 'Critical',
        show_name: 'Yellowstone',
        cost_impact: 50000,
        delay_days: 3,
        url: 'https://jira.example.com/browse/PROD-001'
      }
    ];

    (mcpClient.getProductionIssues as any).mockResolvedValue(mockIssues);

    render(<ProductionTracking />);

    await waitFor(() => {
      expect(screen.getByText('Color grading delays')).toBeInTheDocument();
    });

    expect(screen.getByText('Yellowstone')).toBeInTheDocument();
    expect(screen.getByText(/Critical/i)).toBeInTheDocument();
  });

  it('should render error state when fetch fails', async () => {
    (mcpClient.getProductionIssues as any).mockRejectedValue(
      new Error('Failed to fetch')
    );

    render(<ProductionTracking />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  it('should render empty state when no issues', async () => {
    (mcpClient.getProductionIssues as any).mockResolvedValue([]);

    render(<ProductionTracking />);

    await waitFor(() => {
      expect(screen.getByText(/no production issues/i)).toBeInTheDocument();
    });
  });

  it('should display cost impact for issues', async () => {
    const mockIssues = [
      {
        id: 'PROD-001',
        key: 'PROD-001',
        summary: 'Test issue',
        status: 'Open',
        severity: 'High',
        cost_impact: 75000,
        delay_days: 5,
        url: 'https://jira.example.com/browse/PROD-001'
      }
    ];

    (mcpClient.getProductionIssues as any).mockResolvedValue(mockIssues);

    render(<ProductionTracking />);

    await waitFor(() => {
      expect(screen.getByText(/\$75,000/)).toBeInTheDocument();
    });
  });

  it('should display delay days for issues', async () => {
    const mockIssues = [
      {
        id: 'PROD-001',
        key: 'PROD-001',
        summary: 'Test issue',
        status: 'Open',
        severity: 'High',
        delay_days: 7,
        url: 'https://jira.example.com/browse/PROD-001'
      }
    ];

    (mcpClient.getProductionIssues as any).mockResolvedValue(mockIssues);

    render(<ProductionTracking />);

    await waitFor(() => {
      expect(screen.getByText(/7 days/i)).toBeInTheDocument();
    });
  });
});

