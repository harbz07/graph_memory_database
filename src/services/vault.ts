// ... existing code ...

/**
 * Batch initializes secrets for a project (no-op if key already exists).
 */
export function initializeKeys(keys: string[], project?: string, defaultValue = ""): string[] {
  const vault = loadVault();
  const initialized: string[] = [];
  for (const key of keys) {
    const exists = vault.secrets.some(
      s => s.key === key && (s.project ?? "") === (project ?? "")
    );
    if (!exists) {
      const secret: StoredSecret = {
        key,
        value: defaultValue,
        project,
        createdAt: new Date().toISOString(),
      };
      vault.secrets.push(secret);
      initialized.push(key);
    }
  }
  saveVault(vault);
  return initialized;
}

// ... rest of code ...