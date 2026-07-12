import { useState, useEffect } from 'react'
import keycloak from './keycloak'

function App() {
  const [autenticado, setAutenticado] = useState(false)
  const [pacienteId, setPacienteId] = useState('P000001')
  const [dadosPaciente, setDadosPaciente] = useState(null)
  const [erro, setErro] = useState(null)
  const [carregando, setCarregando] = useState(false)

  useEffect(() => {
    keycloak.init({ onLoad: 'login-required' })
      .then((auth) => {
        setAutenticado(auth)
      })
      .catch(() => {
        setErro('Falha ao inicializar o Keycloak. Verifique se o servidor está online.')
      })
  }, [])

  const buscarPaciente = async () => {
    setErro(null)
    setDadosPaciente(null)
    setCarregando(true)

    try {

      await keycloak.updateToken(30)

      const response = await fetch(`http://localhost:5000/api/pacientes/${pacienteId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${keycloak.token}`,
          'Content-Type': 'application/json'
        }
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.erro || data.error || 'Erro desconhecido ao buscar paciente')
      }

      setDadosPaciente(data)
    } catch (err) {
      setErro(err.message || 'Erro ao processar a requisição.')
    } finally {
      setCarregando(false)
    }
  }

  const fazerLogout = () => {
    keycloak.logout()
  }

  if (!autenticado) {
    return <div style={{ padding: '40px', textAlign: 'center' }}>Redirecionando para o login do hospital...</div>
  }

  return (
    <div style={{ padding: '40px', fontFamily: 'Arial, sans-serif', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Painel Médico - Kiriland</h1>
        <button onClick={fazerLogout} style={{ padding: '8px 15px', backgroundColor: '#dc3545', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          Sair ({keycloak.tokenParsed.preferred_username})
        </button>
      </div>
      
      <div style={{ marginBottom: '20px', padding: '20px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
        <p>Acesso concedido com o perfil: <strong>{keycloak.tokenParsed.realm_access?.roles.join(', ')}</strong></p>

        <label style={{ display: 'block', marginBottom: '10px', fontWeight: 'bold' }}>
          ID do Paciente:
        </label>
        <input 
          type="text" 
          style={{ width: '100%', padding: '10px', marginBottom: '10px', borderRadius: '4px', border: '1px solid #ccc' }}
          value={pacienteId}
          onChange={(e) => setPacienteId(e.target.value)}
        />

        <button 
          onClick={buscarPaciente}
          disabled={carregando}
          style={{ 
            padding: '10px 20px', 
            backgroundColor: carregando ? '#ccc' : '#0056b3', 
            color: '#fff', 
            border: 'none', 
            borderRadius: '4px', 
            cursor: carregando ? 'not-allowed' : 'pointer' 
          }}
        >
          {carregando ? 'Buscando...' : 'Buscar Prontuário'}
        </button>
      </div>

      {erro && (
        <div style={{ padding: '15px', backgroundColor: '#ffebee', color: '#cc0000', borderRadius: '4px', marginBottom: '20px' }}>
          <strong>Acesso Negado ou Erro:</strong> {erro}
        </div>
      )}

      {dadosPaciente && (
        <div style={{ padding: '20px', backgroundColor: '#e8f5e9', border: '1px solid #c8e6c9', borderRadius: '8px' }}>
          <h2 style={{ marginTop: 0 }}>Resultado da API:</h2>
          <pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word', backgroundColor: '#fff', padding: '15px', borderRadius: '4px', border: '1px solid #eee' }}>
            {JSON.stringify(dadosPaciente, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

export default App