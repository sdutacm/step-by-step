// eslint.config.js
import js from "@eslint/js";
import pluginVue from "eslint-plugin-vue";
import prettier from "eslint-config-prettier";
import prettierPlugin from "eslint-plugin-prettier";
import tseslint from "typescript-eslint";
import vueParser from "vue-eslint-parser";
import globals from "globals";

export default [
  // 忽略文件
  {
    ignores: [
      "node_modules/**",
      "dist/**",
      "build/**",
      "public/**",
      "coverage/**",
      "*.config.js",
      "*.config.ts",
      "**/*.d.ts",
    ],
  },

  // 基础配置
  {
    ...js.configs.recommended,
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.es2021,
      },
    },
  },

  // TypeScript 严格类型检查（使用 ts-plugin）
  ...tseslint.configs.strictTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        project: "./tsconfig.json",
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },

  // Vue 文件配置（关键：启用 type-aware linting）
  {
    files: ["**/*.vue"],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tseslint.parser,
        sourceType: "module",
        project: "./tsconfig.json",
        extraFileExtensions: [".vue"],
        // 启用 ts-plugin 类型检查
        __typeAware: true,
      },
      globals: {
        ...globals.browser,
      },
    },
    plugins: {
      vue: pluginVue,
      "@typescript-eslint": tseslint.plugin,
    },
    rules: {
      ...pluginVue.configs["flat/recommended"].rules,
      "vue/multi-word-component-names": "off",

      // 启用 ts-plugin 规则
      "@typescript-eslint/await-thenable": "error",
      "@typescript-eslint/no-floating-promises": "error",
      "@typescript-eslint/no-misused-promises": "error",
      "@typescript-eslint/no-unnecessary-type-assertion": "error",
      "@typescript-eslint/prefer-nullish-coalescing": "error",
      "@typescript-eslint/prefer-optional-chain": "error",
      "@typescript-eslint/prefer-readonly": "error",
    },
  },

  // TypeScript 文件（启用 ts-plugin）
  {
    files: ["**/*.ts", "**/*.tsx"],
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        project: "./tsconfig.json",
        sourceType: "module",
      },
      globals: {
        ...globals.browser,
        ...globals.es2021,
      },
    },
    plugins: {
      "@typescript-eslint": tseslint.plugin,
    },
    rules: {
      // ts-plugin 类型感知规则
      "@typescript-eslint/await-thenable": "error",
      "@typescript-eslint/no-floating-promises": "error",
      "@typescript-eslint/no-misused-promises": "error",
      "@typescript-eslint/no-unnecessary-type-assertion": "error",
      "@typescript-eslint/prefer-nullish-coalescing": "error",
      "@typescript-eslint/prefer-optional-chain": "error",
      "@typescript-eslint/prefer-readonly": "error",
      "@typescript-eslint/switch-exhaustiveness-check": "error",
    },
  },

  // JavaScript 文件
  {
    files: ["**/*.js", "**/*.jsx", "**/*.cjs", "**/*.mjs"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        ...globals.browser,
        ...globals.es2021,
      },
    },
  },

  // Prettier
  prettier,
  {
    files: ["**/*.{vue,ts,tsx,js,jsx,cjs,mjs}"],
    plugins: { prettier: prettierPlugin },
    rules: {
      "prettier/prettier": [
        "error",
        {
          semi: true,
          singleQuote: false,
          tabWidth: 2,
          trailingComma: "es5",
          printWidth: 100,
          endOfLine: "auto",
        },
      ],
    },
  },
];
