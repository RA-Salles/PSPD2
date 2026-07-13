import http from 'k6/http'
import { check, sleep } from 'k6'
import { Rate, Trend } from 'k6/metrics'

const patientLatency = new Trend(
  'patient_latency',
  true
)

const patientErrors = new Rate(
  'patient_errors'
)

export const options = {
  vus: Number(__ENV.VUS || 10),
  duration: __ENV.DURATION || '30s',

  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<5000'],
    patient_errors: ['rate<0.05'],
  },
}

export function setup() {
  const loginResponse = http.post(
    `${__ENV.BASE_URL}/api/login`,
    JSON.stringify({
      username: __ENV.USERNAME,
      password: __ENV.PASSWORD,
    }),
    {
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: '30s',
    }
  )

  const loginValido = check(loginResponse, {
    'login retornou HTTP 200': response =>
      response.status === 200,

    'token foi recebido': response =>
      Boolean(response.json('access_token')),
  })

  if (!loginValido) {
    throw new Error(
      `Login falhou: HTTP ${loginResponse.status} - ` +
      loginResponse.body
    )
  }

  return {
    token: loginResponse.json('access_token'),
  }
}

export default function (data) {
  const response = http.get(
    `${__ENV.BASE_URL}/api/pacientes/P020008105`,
    {
      headers: {
        Authorization: `Bearer ${data.token}`,
      },
      timeout: '30s',
    }
  )

  patientLatency.add(response.timings.duration)
  patientErrors.add(response.status !== 200)

  check(response, {
    'consulta retornou HTTP 200': result =>
      result.status === 200,

    'resposta contém Bundle FHIR': result => {
      if (result.status !== 200) {
        return false
      }

      try {
        return (
          result.json('resposta.resourceType') ===
          'Bundle'
        )
      } catch {
        return false
      }
    },
  })

  sleep(1)
}