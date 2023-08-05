<template>
	<ion-page>
		<ion-content :fullscreen="true">
			<div class="flex flex-col h-screen w-screen">
				<div class="w-full sm:w-96">
					<header
						class="flex flex-row gap-1 bg-white shadow-sm py-4 px-2 items-center border-b sticky top-0 z-10"
					>
						<Button appearance="minimal" class="!px-0 !py-0" @click="router.back()">
							<FeatherIcon name="chevron-left" class="h-5 w-5" />
						</Button>
						<div v-if="id" class="flex flex-row items-center gap-2">
							<h2 class="text-2xl font-semibold text-gray-900">
								Expense Claim
							</h2>
							<Badge :label="id" color="white" />
						</div>
						<h2 v-else class="text-2xl font-semibold text-gray-900">
							New Expense Claim
						</h2>
					</header>

					<!-- Tabs -->
					<div class="bg-white text-sm font-medium text-center text-gray-500 border-b border-gray-200 dark:text-gray-400 dark:border-gray-700">
						<ul class="flex flex-wrap -mb-px">
							<li
								class="mr-2"
								v-for="tab in tabs"
							>
								<button
									@click="activeTab = tab"
									class="inline-block p-4 border-b-2 border-transparent rounded-t-lg"
									:class="activeTab === tab ? 'text-blue-600 border-blue-600 dark:text-blue-500 dark:border-blue-500' : 'hover:text-gray-600 hover:border-gray-300 dark:hover:text-gray-300'"
								>
								{{ tab }}
								</button>
							</li>
						</ul>
					</div>

					<!-- Expenses section -->
					<FormView
						v-if="activeTab === 'Expense Details' && expensesTabFields"
						doctype="Expense Claim"
						v-model="expenseClaim"
						:fields="expensesTabFields"
						:id="props.id"
					/>

					<!-- Advances section -->
					<FormView
						v-if="activeTab === 'Select Advances' && advancesTabFields"
						doctype="Expense Claim"
						v-model="expenseClaim"
						:fields="advancesTabFields"
						:id="props.id"
					/>
				</div>
			</div>
		</ion-content>
	</ion-page>
</template>

<script setup>
import { IonPage, IonContent } from "@ionic/vue"
import { createResource, Badge, FeatherIcon } from "frappe-ui"
import { computed, ref, watch, inject } from "vue"
import { useRouter } from "vue-router"

import FormView from "@/components/FormView.vue"

const router = useRouter()
const dayjs = inject("$dayjs")
const employee = inject("$employee")
const today = dayjs().format("YYYY-MM-DD")
const tabs = ["Expense Details", "Select Advances", "Review Total"]
const activeTab = ref("Expense Details")

const props = defineProps({
	id: {
		type: String,
		required: false,
	},
})

// reactive object to store form data
const expenseClaim = ref({})

// get form fields
const formFields = createResource({
	url: "hrms.api.get_doctype_fields",
	params: { doctype: "Expense Claim" },
	transform(data) {
		let fields = getFilteredFields(data)

		return fields.map((field) => {
			if (field.fieldname === "posting_date") field.default = today

			return field
		})
	},
})
formFields.reload()

const expensesTabIndex = computed(() => {
	return formFields.data?.findIndex((field) => field.fieldname === "taxes")
})
const expensesTabFields = computed(() => {
	return formFields.data?.slice(0, expensesTabIndex.value)
})

const advancesTabIndex = computed(() => {
	return formFields.data?.findIndex((field) => field.fieldname === "advances")
})
const advancesTabFields = computed(() => {
	return formFields.data?.slice(expensesTabIndex.value + 1, advancesTabIndex.value)
})

// form scripts


// helper functions
function getFilteredFields(fields) {
	// reduce noise from the form view by excluding unnecessary fields
	// ex: employee and other details can be fetched from the session user
	const excludeFields = [
		"naming_series",
		"task",
		"remark",
	]

	const employeeFields = ["employee", "employee_name", "department", "company"]

	if (!props.id) excludeFields.push(...employeeFields)

	return fields.filter((field) => !excludeFields.includes(field.fieldname))
}
</script>
