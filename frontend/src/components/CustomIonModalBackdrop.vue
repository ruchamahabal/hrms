<template>
	<div
		class="opacity-25 fixed inset-0 z-40 bg-black"
		@click="() => modalController.dismiss()"
	></div>
</template>

<script setup>
import { modalController } from "@ionic/vue"
</script>
