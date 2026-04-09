# i18n Development Guidelines

Internationalization is currently inactive for this repository.

Use this file only if a frontend is added later and multilingual UI becomes a requirement.

## Rules

1. **Never hardcode user-facing strings** in UI components. Always use the translation function.

2. **Import pattern** (adapt to your i18n library):
   ```tsx
   // React + react-i18next example:
   import { useTranslation } from 'react-i18next';
   const { t } = useTranslation();
   return <p>{t('namespace.key')}</p>;
   ```

3. **When creating new UI text**, add the translation key to ALL locale files.

4. **Key naming convention** — use dot-separated namespaces:
   - `sidebar.*`, `chat.*`, `dialog.*`, `common.*`, `errors.*`, etc.

5. **Interpolation** — for dynamic values:
   ```tsx
   t('errors.maxCount', { count: 5 })
   // en.json: "Maximum {{count}} items allowed."
   ```

6. **Date formatting** — use locale-aware formatting.

7. **Provide real translations** — do not leave placeholder text.

## Configuration

- Locale files location: `N/A (inactive)`
- i18n config location: `N/A (inactive)`
- Supported locales: `N/A (inactive)`
