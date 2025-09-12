export type AmplifyAuthConfig = {
  Auth: {
    Cognito: {
      userPoolId: string
      userPoolClientId: string
      loginWith?: {
        email?: boolean
        username?: boolean
        phone?: boolean
      }
    }
    oauth?: {
      domain: string
      redirectSignIn: string[]
      redirectSignOut: string[]
      scope: string[]
      responseType: 'code'
    }
  }
}

export function getAmplifyConfig(): AmplifyAuthConfig {
  const userPoolId = process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID || ''
  const clientId = process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID || ''
  const domain = process.env.NEXT_PUBLIC_COGNITO_DOMAIN || ''
  const redirectSignIn = (process.env.NEXT_PUBLIC_COGNITO_REDIRECT_SIGN_IN || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
  const redirectSignOut = (process.env.NEXT_PUBLIC_COGNITO_REDIRECT_SIGN_OUT || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
  const scope = (process.env.NEXT_PUBLIC_COGNITO_SCOPES || 'openid,email,profile')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)

  const config: any = {
    Auth: {
      Cognito: {
        userPoolId,
        userPoolClientId: clientId,
        loginWith: {
          email: true,
          username: false,
          phone: false,
        },
      },
    },
  }

  if (domain) {
    config.Auth.oauth = {
      domain,
      redirectSignIn: redirectSignIn.length ? redirectSignIn : ['http://localhost:3000/auth/callback'],
      redirectSignOut: redirectSignOut.length ? redirectSignOut : ['http://localhost:3000/'],
      scope,
      responseType: 'code',
    }
  }

  return config as AmplifyAuthConfig
}


