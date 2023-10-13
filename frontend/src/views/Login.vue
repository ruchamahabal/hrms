<template>
	<ion-page>
		<ion-content class="ion-padding">
			<div class="flex h-screen w-screen flex-col justify-center bg-white">
				<Dialog
					:options="{
						title: 'Login Failed',
						message: 'No employee found associated with this email ID. Try logging in with your employee email ID or contact your HR manager for access.',
						size: 'lg',
					}"
					v-model="showDialog"
					@onClose="() => session.isInvalidEmployee = false"
				/>

				<div class="flex flex-col mx-auto gap-3 items-center">
					<FrappeHRLogo class="h-8 w-8" />
					<div class="text-3xl font-semibold text-gray-900 text-center">
						Login to Frappe HR
					</div>
				</div>

				<div class="mx-auto mt-10 w-full px-8 sm:w-96">
					<form class="flex flex-col space-y-4" @submit.prevent="submit">
						<Input
							label="Email"
							placeholder="johndoe@mail.com"
							v-model="email"
							:type="email !== 'Administrator' ? 'email' : 'text'"
						/>
						<Input
							label="Password"
							type="password"
							placeholder="••••••"
							v-model="password"
						/>
						<ErrorMessage :message="session.login.error" />
						<Button
							:loading="session.login.loading"
							variant="solid"
							class="disabled:bg-gray-700 disabled:text-white !mt-6"
						>
							Login
						</Button>
					</form>
				</div>
			</div>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { inject, ref, computed } from "vue"
import { Input, Button, ErrorMessage, Dialog } from "frappe-ui"

import FrappeHRLogo from "@/components/icons/FrappeHRLogo.vue";

const email = ref(null)
const password = ref(null)

const session = inject("$session")
const showDialog = ref(session.isInvalidEmployee)

function submit(e) {
	session.login.submit({
		email: email.value,
		password: password.value,
	})
}
</script>
