<template>
  <main class="flex min-h-screen items-center justify-center bg-gray-50 px-6 text-center">
    <div>
      <p class="text-8xl font-black text-blue-600">404</p>
      <h1 class="mt-4 text-3xl font-bold text-gray-900">Page not found</h1>
      <p class="mt-2 text-gray-600">The page you are looking for does not exist.</p>
      <RouterLink
        to="/"
        class="btn-primary mt-8 inline-flex justify-center"
      >
        ← Back to dashboard
      </RouterLink>
    </div>
  </main>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>
