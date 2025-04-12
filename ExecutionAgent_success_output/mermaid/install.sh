#!/bin/bash

# Ensure the script is executed in the script's directory
cd "$(dirname "$0")"

# Step 1: Install pnpm globally
npm install -g pnpm

# Step 2: Install project dependencies
pnpm install --frozen-lockfile

# Step 3: Run unit tests with coverage
pnpm test:coverage

# Step 4: Run ganttDb tests
pnpm exec vitest run ./packages/mermaid/src/diagrams/gantt/ganttDb.spec.ts --coverage

# Step 5: Verify TypeScript build
pnpm test:check:tsc

echo "Setup and tests completed."