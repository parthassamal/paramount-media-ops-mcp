/**
 * Unit tests for MCP API client.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mcpClient } from '../mcpClient';

// Mock fetch globally
global.fetch = vi.fn();

describe('mcpClient', () => {
  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks();
  });

  describe('getProductionIssues', () => {
    it('should fetch production issues successfully', async () => {
      const mockIssues = [
        {
          id: 'PROD-001',
          key: 'PROD-001',
          summary: 'Test issue',
          status: 'Open',
          severity: 'High',
          cost_impact: 50000,
          delay_days: 3
        }
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockIssues
      });

      const issues = await mcpClient.getProductionIssues();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/jira/issues')
      );
      expect(issues).toEqual(mockIssues);
    });

    it('should handle fetch errors', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      await expect(mcpClient.getProductionIssues()).rejects.toThrow('Network error');
    });

    it('should handle non-ok responses', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'
      });

      await expect(mcpClient.getProductionIssues()).rejects.toThrow();
    });
  });

  describe('getChurnCohorts', () => {
    it('should fetch churn cohorts successfully', async () => {
      const mockCohorts = [
        {
          cohort_name: 'High Risk',
          subscriber_count: 50000,
          churn_probability: 0.85,
          risk_level: 'High',
          revenue_at_risk: 1000000
        }
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockCohorts
      });

      const cohorts = await mcpClient.getChurnCohorts();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/analytics/churn/cohorts')
      );
      expect(cohorts).toEqual(mockCohorts);
    });
  });

  describe('getQoEMetrics', () => {
    it('should fetch QoE metrics successfully', async () => {
      const mockMetrics = [
        {
          metric_name: 'buffering_rate',
          value: 1.2,
          threshold: 2.0,
          status: 'good',
          unit: 'percentage'
        }
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockMetrics
      });

      const metrics = await mcpClient.getQoEMetrics();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/streaming/qoe/metrics')
      );
      expect(metrics).toEqual(mockMetrics);
    });
  });

  describe('getServiceHealth', () => {
    it('should fetch service health successfully', async () => {
      const mockServices = [
        {
          service_name: 'API Gateway',
          status: 'healthy',
          response_time_ms: 45,
          error_rate: 0.01,
          throughput_rpm: 5000
        }
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockServices
      });

      const services = await mcpClient.getServiceHealth();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/streaming/infrastructure/services')
      );
      expect(services).toEqual(mockServices);
    });
  });

  describe('Error handling', () => {
    it('should throw error for 404 responses', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found'
      });

      await expect(mcpClient.getProductionIssues()).rejects.toThrow();
    });

    it('should throw error for 500 responses', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'
      });

      await expect(mcpClient.getProductionIssues()).rejects.toThrow();
    });
  });
});


