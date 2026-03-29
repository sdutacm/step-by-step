import { defineStore } from 'pinia'
import { getCurrentUser } from '../api/auth'
import type { User } from '../api/auth'

interface UserState {
  user: User | null
  isSuperAdmin: boolean
  loading: boolean
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    user: null,
    isSuperAdmin: false,
    loading: false,
  }),

  actions: {
    async fetchUser() {
      this.loading = true
      try {
        const user = await getCurrentUser()
        this.user = user
        this.isSuperAdmin = 'is_super_admin' in user ? (user as User & { is_super_admin: boolean }).is_super_admin : false
      } catch {
        this.user = null
        this.isSuperAdmin = false
      } finally {
        this.loading = false
      }
    },

    setUser(user: User | null) {
      this.user = user
      if (user && 'is_super_admin' in user) {
        this.isSuperAdmin = (user as User & { is_super_admin: boolean }).is_super_admin
      } else {
        this.isSuperAdmin = false
      }
    },

    clearUser() {
      this.user = null
      this.isSuperAdmin = false
    },
  },
})
