import frappe
from frappe.utils import cint, flt
from frappe.model.document import Document

from erpnext import get_company_currency
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
)

class PayrollAccrual:
	def __init__(self, payroll_entry: Document, submitted_salary_slips: list):
		self.check_permission("write")

		self.payroll_entry = payroll_entry
		self.submitted_salary_slips = submitted_salary_slips

		self._payable_amount = 0
		self._employee_wise_payroll_payable_entries = {}
		self._accounting_dimensions = get_accounting_dimensions()
		self._company_currency = get_company_currency(self.payroll_entry.company)
		self._is_employee_wise_accounting_enabled = frappe.db.get_single_value(
			"Payroll Settings", "process_payroll_accounting_entry_based_on_employee"
		)
		self._accounts = []
		self._currencies = []

	def prepare_accrual_entry(self):
		self._advance_deduction_entries = []

		earnings = self.get_component_wise_amounts("earnings")
		deductions = self.get_component_wise_amounts("deductions")

		if not (earnings or deductions):
			frappe.throw(_("Please set default accounts in Salary Components"))

		precision = frappe.get_precision("Journal Entry Account", "debit_in_account_currency")

		payable_amount = self.get_payable_amount_for_earnings_and_deductions(
			accounts,
			earnings,
			deductions,
			currencies,
			company_currency,
			accounting_dimensions,
			precision,
			payable_amount,
		)
		self.set_accounts()
		self.set_accounts()

		for entry in self._advance_deduction_entries:
			payable_amount = self.get_accounting_entries_and_payable_amount(
				entry.get("account"),
				entry.get("cost_center"),
				entry.get("amount"),
				currencies,
				company_currency,
				payable_amount,
				accounting_dimensions,
				precision,
				entry_type="credit",
				accounts=accounts,
				party=entry.get("employee"),
				reference_type="Employee Advance",
				reference_name=entry.get("reference_name"),
				is_advance="Yes",
			)

		self.set_payable_amount_against_payroll_payable_account(
			accounts,
			currencies,
			company_currency,
			accounting_dimensions,
			precision,
			payable_amount,
			self.payroll_payable_account,
			employee_wise_accounting_enabled,
		)

		self.payroll_entry.make_journal_entry(
			accounts,
			currencies,
			self.payroll_payable_account,
			voucher_type="Journal Entry",
			user_remark=_("Accrual Journal Entry for salaries from {0} to {1}").format(
				self.start_date, self.end_date
			),
			submit_journal_entry=True,
			submitted_salary_slips=self.submitted_salary_slips,
		)

	def get_component_wise_amounts(self, component_type: str) -> dict:
		salary_components = self.get_salary_components(component_type)
		component_dict = {}

		for item in salary_components:
			if not self.should_add_component_to_accrual_jv(component_type, item):
				continue

			employee_cost_centers = self.payroll_entry.get_payroll_cost_centers_for_employee(
				item.employee, item.salary_structure
			)
			employee_advance = self.get_advance_deduction(component_type, item)

			for cost_center, percentage in employee_cost_centers.items():
				amount_against_cost_center = flt(item.amount) * percentage / 100

				if employee_advance:
					self.add_advance_deduction_entry(item, amount_against_cost_center, cost_center, employee_advance)
				else:
					key = (item.salary_component, cost_center)
					component_dict[key] = component_dict.get(key, 0) + amount_against_cost_center

				if self._is_employee_wise_accounting_enabled:
					self.set_employee_wise_payroll_payable_entries(
						component_type, item.employee, amount_against_cost_center
					)

		account_details = self.get_component_accounts(component_dict=component_dict)

		return account_details

	def get_component_accounts(self, component_dict: dict = None) -> dict:
		"""
		Returns an account dict from component dict by consolidating component amounts by accounts:
		from component_dict: {("Basic - F", "Main Cost Center - F"): 1000, ("HRA - F", "Main Cost Center - F"): 1000}
		to account dict: {("Salary Expenses - F", "Main Cost Center - F"): 2000}
		"""
		account_dict = {}

		for component_tuple, amount in component_dict.items():
			account = self.get_salary_component_account(component_tuple[0])
			accounting_key = (account, component_tuple[1])

			account_dict[accounting_key] = account_dict.get(accounting_key, 0) + amount

		return account_dict

	def get_salary_components(self, component_type: str) -> list:
		salary_slips = self.payroll_entry.get_sal_slip_list(ss_status=1, as_dict=True)

		if not salary_slips:
			return []

		ss = frappe.qb.DocType("Salary Slip")
		ssd = frappe.qb.DocType("Salary Detail")
		salary_components = (
			frappe.qb.from_(ss)
			.join(ssd)
			.on(ss.name == ssd.parent)
			.select(
				ssd.salary_component,
				ssd.amount,
				ssd.parentfield,
				ssd.additional_salary,
				ss.salary_structure,
				ss.employee,
			)
			.where((ssd.parentfield == component_type) & (ss.name.isin([d.name for d in salary_slips])))
		).run(as_dict=True)

		return salary_components

	def should_add_component_to_accrual_jv(self, component_type: str, item: dict) -> bool:
		add_component_to_accrual_jv = True
		if component_type == "earnings":
			is_flexible_benefit, only_tax_impact = frappe.get_cached_value(
				"Salary Component", item["salary_component"], ["is_flexible_benefit", "only_tax_impact"]
			)
			if cint(is_flexible_benefit) and cint(only_tax_impact):
				add_component_to_accrual_jv = False

		return add_component_to_accrual_jv

	def add_advance_deduction_entry(
		self,
		item: dict,
		amount: float,
		employee_advance: str,
		cost_center: str = None,
	) -> None:
		self._advance_deduction_entries.append(
			{
				"employee": item.employee,
				"account": self.get_salary_component_account(item.salary_component),
				"amount": amount_against_cost_center,
				"cost_center": cost_center,
				"reference_type": "Employee Advance",
				"reference_name": employee_advance,
			}
		)

	def get_salary_component_account(self, salary_component: str):
		account = frappe.db.get_value(
			"Salary Component Account",
			{"parent": salary_component, "company": self.payroll_entry.company},
			"account",
			cache=True,
		)

		if not account:
			frappe.throw(
				_("Please set account in Salary Component {0}").format(
					get_link_to_form("Salary Component", salary_component)
				)
			)

		return account

	def set_employee_wise_payroll_payable_entries(
		self,
		component_type,
		employee,
		amount,
		salary_structure=None
	):
		employee_details = self._employee_wise_payroll_payable_entries.setdefault(employee, {})

		employee_details.setdefault(component_type, 0)
		employee_details[component_type] += amount

		if salary_structure and "salary_structure" not in employee_details:
			employee_details["salary_structure"] = salary_structure


	def set_accounts_for(self, components: dict, component_type: str) -> None:
		# Earnings
		for key, amount in components.items():
			account, cost_center = key

			self.get_accounting_entries_and_payable_amount(
				account,
				cost_center or self.cost_center,
				amount,
				currencies,
				company_currency,
				payable_amount,
				accounting_dimensions,
				precision,
				entry_type="debit",
				accounts=accounts,
			)

		# Deductions
		for acc_cc, amount in deductions.items():
			payable_amount = self.get_accounting_entries_and_payable_amount(
				acc_cc[0],
				acc_cc[1] or self.cost_center,
				amount,
				currencies,
				company_currency,
				payable_amount,
				accounting_dimensions,
				precision,
				entry_type="credit",
				accounts=accounts,
			)

		return payable_amount

	def get_accounting_entries_and_payable_amount(
		self,
		account,
		cost_center,
		amount,
		currencies,
		company_currency,
		payable_amount,
		accounting_dimensions,
		precision,
		entry_type="credit",
		party=None,
		accounts=None,
		reference_type=None,
		reference_name=None,
		is_advance=None,
	):
		exchange_rate, amt = self.get_amount_and_exchange_rate_for_journal_entry(
			account, amount, company_currency, currencies
		)

		row = {
			"account": account,
			"exchange_rate": flt(exchange_rate),
			"cost_center": cost_center,
			"project": self.project,
		}

		if entry_type == "debit":
			payable_amount += flt(amount, precision)
			row.update(
				{
					"debit_in_account_currency": flt(amt, precision),
				}
			)
		elif entry_type == "credit":
			payable_amount -= flt(amount, precision)
			row.update(
				{
					"credit_in_account_currency": flt(amt, precision),
				}
			)
		else:
			row.update(
				{
					"credit_in_account_currency": flt(amt, precision),
					"reference_type": self.doctype,
					"reference_name": self.name,
				}
			)

		if party:
			row.update(
				{
					"party_type": "Employee",
					"party": party,
				}
			)
		if reference_type:
			row.update(
				{
					"reference_type": reference_type,
					"reference_name": reference_name,
					"is_advance": is_advance,
				}
			)

		self.update_accounting_dimensions(
			row,
			accounting_dimensions,
		)

		if amt:
			accounts.append(row)

		return payable_amount

	def update_accounting_dimensions(self, row, accounting_dimensions):
		for dimension in accounting_dimensions:
			row.update({dimension: self.get(dimension)})

		return row

	def get_amount_and_exchange_rate_for_journal_entry(
		self, account, amount, company_currency, currencies
	):
		conversion_rate = 1
		exchange_rate = self.exchange_rate
		account_currency = frappe.db.get_value("Account", account, "account_currency", cache=True)

		if account_currency not in currencies:
			currencies.append(account_currency)

		if account_currency == company_currency:
			conversion_rate = self.exchange_rate
			exchange_rate = 1

		amount = flt(amount) * flt(conversion_rate)

		return exchange_rate, amount
