import { type NextRequest, NextResponse } from 'next/server'
import { handleSignIn } from 'aws-amplify/nextjs'

export async function GET(request: NextRequest) {
  return handleSignIn(request)
}


