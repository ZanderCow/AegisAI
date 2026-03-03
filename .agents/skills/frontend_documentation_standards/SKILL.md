---
name: Frontend Documentation Standards
description: Apply comprehensive React, Vite, and TypeScript documentation standards across the frontend codebase
---

# React and Vite Documentation Standards

This skill defines the strict documentation standards required for the frontend codebase, which utilizes React 19, Vite, TypeScript, and Tailwind CSS. Adhering to these standards ensures the codebase remains maintainable, readable, and maximizes developer experience through IntelliSense.

## 1. Component Documentation (TSDoc/JSDoc)

All React components must be documented using TSDoc/JSDoc comment blocks immediately preceding the component definition.
- Use `/** ... */` for comments.
- Start with a clear, concise description of the component's purpose and usage.
- Document any important state or side-effects (hooks usage) if they are complex.

### Component Documentation Example
```tsx
import React from 'react';

/**
 * Renders a primary call-to-action button with loading state support.
 * 
 * This component wraps the standard HTML button and applies Tailwind CSS
 * classes for consistent branding.
 */
export const PrimaryButton: React.FC<PrimaryButtonProps> = ({ 
  label, 
  isLoading, 
  onClick 
}) => {
  // ...
};
```

## 2. Props Documentation

All component props must be defined using TypeScript `interface` or `type` aliases. Each property within the interface must have a TSDoc comment explaining its purpose, expected values, and whether it's optional.

### Props Documentation Example
```tsx
/**
 * Props for the PrimaryButton component.
 */
export interface PrimaryButtonProps {
  /** The text displayed inside the button. */
  label: string;
  
  /** 
   * Indicates whether the button is in a loading state. 
   * If true, a spinner is displayed and the button is disabled.
   * @default false
   */
  isLoading?: boolean;
  
  /** Callback function executed when the button is clicked. */
  onClick: () => void;
}
```

## 3. Hook and Utility Documentation

Custom React hooks and utility functions must also be fully documented with TSDoc, explicitly defining arguments (`@param`) and return values (`@returns`).

### Hook Documentation Example
```ts
/**
 * Custom hook to manage the local storage state.
 *
 * @param key - The local storage key to read/write.
 * @param initialValue - The default value if the key does not exist.
 * @returns A stateful value and a function to update it.
 */
export function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T) => void] {
  // ...
}
```

## 4. File Naming and Structure

- **Components:** Use PascalCase for both component names and their filenames (e.g., `PrimaryButton.tsx`).
- **Hooks:** Use camelCase starting with "use" (e.g., `useLocalStorage.ts`).
- **Utilities:** Use camelCase or kebab-case (e.g., `format-date.ts`).

## Instructions for Execution

When you are asked to apply this skill to frontend code:
1. Review the target `.tsx` or `.ts` file(s).
2. Ensure every exported component, interface, type alias, hook, and significant utility function has a valid TSDoc/JSDoc comment block.
3. Validate that strict TypeScript typing is used for all props, function arguments, and return values.
4. Ensure the component adheres to modern React functional component patterns using Hooks.
5. Apply the standard naming conventions.
6. Commit or write the changes back to the target files securely, ensuring no existing functionality is broken.
