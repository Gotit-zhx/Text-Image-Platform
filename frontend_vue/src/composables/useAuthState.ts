import { computed, ref } from 'vue'
import type { LoginUser } from '../types'
import { authConfigApi, loginApi, logoutApi, meApi, registerApi, type AuthConfig } from '../api/auth'
import { clearSessionUser, readSessionUser, writeSessionUser } from '../auth/session'

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
  const authPending = ref(false)
  const authError = ref('')
  const authMessage = ref('')
  const authReady = ref(false)
  const authConfig = ref<AuthConfig>({ registrationEnabled: false, emailAvailable: false })
  const loginUser = ref<LoginUser | null>(readSessionUser())

  const canLogin = computed(() => account.value.trim() !== '' && password.value.trim() !== '')
  const isLoggedIn = computed(() => !!loginUser.value)
  const isRegisterEmailValid = computed(() =>
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerEmail.value)
  )
  const isRegisterPasswordMatch = computed(
    () =>
      registerPassword.value.trim() !== '' &&
      registerConfirmPassword.value.trim() !== '' &&
      registerPassword.value === registerConfirmPassword.value
  )
  const canRegister = computed(() => authConfig.value.registrationEnabled && isRegisterEmailValid.value && isRegisterPasswordMatch.value)

  const openLoginModal = () => {
    if (isLoggedIn.value) return
    showLoginModal.value = true
    showRegisterModal.value = false
  }

  const closeLoginModal = () => {
    showLoginModal.value = false
  }

  const openRegisterModal = () => {
    if (!authConfig.value.registrationEnabled) return
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

  const submitLogin = async () => {
    if (!canLogin.value || authPending.value) return
    authPending.value = true
    authError.value = ''
    authMessage.value = ''
    try {
      loginUser.value = await loginApi(account.value, password.value, getUserStats())
      writeSessionUser(loginUser.value)
      password.value = ''
      closeLoginModal()
    } catch (e) {
      authError.value = e instanceof Error ? e.message : '登录失败'
    } finally {
      authPending.value = false
    }
  }
  const submitRegister = async () => {
    if (!canRegister.value || authPending.value) return
    authPending.value = true
    authError.value = ''
    authMessage.value = ''
    try {
      const result = await registerApi(registerEmail.value, registerPassword.value)
      authMessage.value = result.message
      registerPassword.value = ''
      registerConfirmPassword.value = ''
    } catch (e) {
      authError.value = e instanceof Error ? e.message : '注册失败'
    } finally {
      authPending.value = false
    }
  }
  const submitLogout = async () => {
    await logoutApi()
    loginUser.value = null
    for (const key of Object.keys(localStorage))
      if (key.startsWith('baicaoyuan-recovery:')) localStorage.removeItem(key)
    clearSessionUser()
  }

  const refreshSession = async () => {
    const config = authConfigApi().then((value) => { authConfig.value = value }).catch(() => {
      authConfig.value = { registrationEnabled: false, emailAvailable: false }
    })
    try {
      const user = await meApi()
      loginUser.value = user
      writeSessionUser(user)
    } catch {
      loginUser.value = null
      clearSessionUser()
    } finally {
      await config
      authReady.value = true
    }
  }

  return {
    showLoginModal,
    showRegisterModal,
    account,
    password,
    registerEmail,
    registerPassword,
    registerConfirmPassword,
    authPending,
    authError,
    authMessage,
    authReady,
    authConfig,
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
    submitLogin,
    submitRegister,
    submitLogout,
    refreshSession
  }
}
