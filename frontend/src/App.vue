<template>
	<ion-app>
		<ion-router-outlet id="main-content" />
		<Menu v-if="!menu.disabled"/>
		<Toasts />

		<!-- <InstallPrompt /> -->
	</ion-app>
</template>

<script setup>
import { IonApp, IonRouterOutlet } from "@ionic/vue"

import { Toasts } from "frappe-ui"

import Menu from "@/components/Menu.vue"
import InstallPrompt from "@/components/InstallPrompt.vue"
import { menu } from "@/data/menu"
</script>
