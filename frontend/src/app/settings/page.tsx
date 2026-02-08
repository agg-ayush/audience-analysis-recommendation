"use client";

import { useEffect, useState } from "react";
import { Nav } from "@/components/nav";
import { api, type SettingsResponse } from "@/lib/api";

type FieldConfig = {
  key: keyof SettingsResponse;
  label: string;
  type: "float" | "int" | "pct";
  group: string;
};

const FIELDS: FieldConfig[] = [
  // Noise filters
  { key: "min_spend", label: "Min spend (INR)", type: "float", group: "Noise Filters" },
  { key: "min_purchases", label: "Min purchases", type: "int", group: "Noise Filters" },
  { key: "min_age_days", label: "Min age (days)", type: "int", group: "Noise Filters" },
  // Performance buckets
  { key: "winner_threshold", label: "Winner threshold (normalized ROAS)", type: "float", group: "Performance Buckets" },
  { key: "loser_threshold", label: "Loser threshold (normalized ROAS)", type: "float", group: "Performance Buckets" },
  // Trend
  { key: "improving_slope", label: "Improving slope", type: "float", group: "Trend Thresholds" },
  { key: "declining_slope", label: "Declining slope", type: "float", group: "Trend Thresholds" },
  { key: "volatile_cpa_std", label: "Volatile CPA std dev", type: "float", group: "Trend Thresholds" },
  // Scoring weights
  { key: "roas_weight", label: "ROAS weight", type: "float", group: "Scoring Weights" },
  { key: "spend_weight", label: "Spend weight", type: "float", group: "Scoring Weights" },
  { key: "cvr_weight", label: "CVR weight", type: "float", group: "Scoring Weights" },
  { key: "volume_weight", label: "Volume weight", type: "float", group: "Scoring Weights" },
  // Guardrails
  { key: "max_scale_pct", label: "Max scale %", type: "int", group: "Guardrails" },
  { key: "scale_cooldown_hours", label: "Scale cooldown (hours)", type: "int", group: "Guardrails" },
  { key: "max_daily_budget_increase", label: "Max daily budget increase (INR)", type: "float", group: "Guardrails" },
  // Audience modifiers
  { key: "broad_roas_threshold_multiplier", label: "Broad: ROAS threshold multiplier", type: "float", group: "Audience Modifiers" },
  { key: "broad_min_days_before_pause", label: "Broad: min days before pause", type: "int", group: "Audience Modifiers" },
  { key: "lla_scale_pct_bump", label: "LLA: scale % bump", type: "int", group: "Audience Modifiers" },
  { key: "lla_fatigue_spend_multiplier", label: "LLA: fatigue spend multiplier", type: "float", group: "Audience Modifiers" },
  { key: "interest_days_decline_before_pause", label: "Interest: days decline before pause", type: "int", group: "Audience Modifiers" },
  { key: "custom_max_scale_pct", label: "Custom: max scale %", type: "int", group: "Audience Modifiers" },
];

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [original, setOriginal] = useState<SettingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const loadSettings = () => {
    setLoading(true);
    api
      .getSettings()
      .then((s) => {
        setSettings(s);
        setOriginal(s);
      })
      .catch(() => setSettings(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const handleChange = (key: keyof SettingsResponse, value: string) => {
    if (!settings) return;
    const num = value === "" ? 0 : Number(value);
    setSettings({ ...settings, [key]: num });
  };

  const hasChanges =
    settings && original
      ? FIELDS.some((f) => settings[f.key] !== original[f.key])
      : false;

  const handleSave = () => {
    if (!settings || !original) return;
    setSaving(true);
    setMessage(null);

    // Only send changed fields
    const diff: Partial<SettingsResponse> = {};
    for (const f of FIELDS) {
      if (settings[f.key] !== original[f.key]) {
        (diff as Record<string, number>)[f.key] = settings[f.key];
      }
    }

    api
      .updateSettings(diff)
      .then((s) => {
        setSettings(s);
        setOriginal(s);
        setMessage({ type: "success", text: "Settings saved." });
      })
      .catch((e) => setMessage({ type: "error", text: `Save failed: ${e.message}` }))
      .finally(() => setSaving(false));
  };

  const handleReset = () => {
    setSaving(true);
    setMessage(null);
    api
      .resetSettings()
      .then((s) => {
        setSettings(s);
        setOriginal(s);
        setMessage({ type: "success", text: "Settings reset to defaults." });
      })
      .catch((e) => setMessage({ type: "error", text: `Reset failed: ${e.message}` }))
      .finally(() => setSaving(false));
  };

  const groups = Array.from(new Set(FIELDS.map((f) => f.group)));

  return (
    <div className="min-h-screen bg-background">
      <Nav />
      <main className="mx-auto max-w-2xl px-4 py-6">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold">Settings</h1>
          <div className="flex gap-2">
            <button
              onClick={handleReset}
              disabled={saving}
              className="rounded-lg border border-input px-4 py-2 text-sm font-medium hover:bg-muted disabled:opacity-50"
            >
              Reset to defaults
            </button>
            <button
              onClick={handleSave}
              disabled={saving || !hasChanges}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 disabled:opacity-50"
            >
              {saving ? "Saving…" : "Save changes"}
            </button>
          </div>
        </div>

        {message && (
          <div
            className={`mb-4 rounded-lg border p-3 text-sm ${
              message.type === "success"
                ? "border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                : "border-red-300 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-950 dark:text-red-300"
            }`}
          >
            {message.text}
          </div>
        )}

        {loading ? (
          <p className="text-muted-foreground">Loading…</p>
        ) : settings ? (
          <div className="space-y-6">
            {groups.map((group) => (
              <div key={group} className="rounded-lg border border-border bg-card p-6">
                <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                  {group}
                </h2>
                <div className="space-y-3">
                  {FIELDS.filter((f) => f.group === group).map((f) => {
                    const value = settings[f.key];
                    const changed = original && value !== original[f.key];
                    return (
                      <div key={String(f.key)} className="flex items-center justify-between gap-4">
                        <label className="text-sm text-foreground" htmlFor={String(f.key)}>
                          {f.label}
                        </label>
                        <input
                          id={String(f.key)}
                          type="number"
                          step={f.type === "int" ? 1 : 0.01}
                          value={value}
                          onChange={(e) => handleChange(f.key, e.target.value)}
                          className={`w-28 rounded-md border px-3 py-1.5 text-right text-sm ${
                            changed
                              ? "border-primary bg-primary/5 font-medium"
                              : "border-input bg-background"
                          }`}
                        />
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground">Could not load settings. Is the backend running?</p>
        )}
      </main>
    </div>
  );
}
