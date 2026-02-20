import { computed, ref } from 'vue'
import type { LoginUser } from '../types'
import { loginApi, registerApi } from '../api/auth'

type UseAuthStateOptions = {
	getUserStats: () => { fans: number; follows: number }
}

export const useAuthState = ({ getUserStats }: UseAuthStateOptions) => {
	const showLoginModal = ref(false)
	const showRegisterModal = ref(false)
	const account = ref('')
	const password = ref('')
	const registerEmail = ref('')
	const registerPassword = ref('')
	const registerConfirmPassword = ref('')
	const userPassword = ref('123456')
	const loginUser = ref<LoginUser | null>(null)

	const canLogin = computed(() => account.value.trim() !== '' && password.value.trim() !== '')
	const isLoggedIn = computed(() => !!loginUser.value)
	const isRegisterEmailValid = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerEmail.value))
	const isRegisterPasswordMatch = computed(
		() =>
			registerPassword.value.trim() !== '' &&
			registerConfirmPassword.value.trim() !== '' &&
			registerPassword.value === registerConfirmPassword.value
	)
	const canRegister = computed(() => isRegisterEmailValid.value && isRegisterPasswordMatch.value)

	const openLoginModal = () => {
		if (isLoggedIn.value) return
		showLoginModal.value = true
		showRegisterModal.value = false
	}

	const closeLoginModal = () => {
		showLoginModal.value = false
	}

	const openRegisterModal = () => {
		showLoginModal.value = false
		showRegisterModal.value = true
	}

	const closeRegisterModal = () => {
		showRegisterModal.value = false
	}

	const backToLogin = () => {
		showRegisterModal.value = false
		showLoginModal.value = true
	}

	const mockLogin = async () => {
		if (!canLogin.value) return
		loginUser.value = await loginApi(account.value, getUserStats())
		closeLoginModal()
	}

	const mockRegister = async () => {
		if (!canRegister.value) return
		loginUser.value = await registerApi(registerEmail.value, getUserStats())
		closeRegisterModal()
	}

	const mockLogout = () => {
		loginUser.value = null
	}

	return {
		showLoginModal,
		showRegisterModal,
		account,
		password,
		registerEmail,
		registerPassword,
		registerConfirmPassword,
		userPassword,
		loginUser,
		canLogin,
		isLoggedIn,
		isRegisterEmailValid,
		isRegisterPasswordMatch,
		canRegister,
		openLoginModal,
		closeLoginModal,
		openRegisterModal,
		closeRegisterModal,
		backToLogin,
		mockLogin,
		mockRegister,
		mockLogout
	}
}
