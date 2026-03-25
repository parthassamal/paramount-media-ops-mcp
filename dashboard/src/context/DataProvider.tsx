import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { API_BASE } from "../config/api";

type HealthData = Record<string, any>;
type JiraIssue = Record<string, any>;

interface DataContextType {
  health: HealthData | null;
  issues: JiraIssue[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

const DataContext = createContext<DataContextType>({
  health: null,
  issues: [],
  loading: true,
  error: null,
  refresh: () => {},
});

export function useAppData() {
  return useContext(DataContext);
}

const POLL_INTERVAL_MS = 30_000;

export function DataProvider({ children }: { children: React.ReactNode }) {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [issues, setIssues] = useState<JiraIssue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      const [healthRes, issuesRes] = await Promise.all([
        fetch(`${API_BASE}/health`),
        fetch(`${API_BASE}/api/jira/issues`),
      ]);
      if (healthRes.ok) setHealth(await healthRes.json());
      if (issuesRes.ok) setIssues(await issuesRes.json());
      setError(null);
    } catch (err: any) {
      setError(err?.message || "Failed to fetch data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchAll]);

  return (
    <DataContext.Provider value={{ health, issues, loading, error, refresh: fetchAll }}>
      {children}
    </DataContext.Provider>
  );
}
