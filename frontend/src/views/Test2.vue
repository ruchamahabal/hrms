<template>
	<BaseLayout>
		<template #body>
			<div
				class="flex flex-col items-center content-center justify-center h-screen"
			>
				<h2 class="text-2xl font-bold">Second View</h2>
				<router-link :to="{ name: 'Test1' }">Go to the First View</router-link>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import BaseLayout from '@/components/BaseLayout.vue';
</script>
