<template>
	<BaseLayout pageTitle="Profile">
		<template #body>
			<div
				class="flex flex-col items-center content-center justify-center h-screen"
			>
				<h2 class="text-2xl font-bold">First View</h2>
				<router-link :to="{ name: 'Test2' }">Go to the Second View</router-link>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import BaseLayout from "@/components/BaseLayout.vue"
</script>
