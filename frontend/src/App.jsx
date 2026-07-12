import { useState } from 'react'

function App() {
  const [username, setUsername] = useState('med.cardoso')
  const [password, setPassword] = useState('PseudoPEP2026!')
  const [token, setToken] = useState(null)
  
  const [pacienteId, setPacienteId] = useState('P000001')
  const [dadosPaciente, setDadosPaciente] = useState(null)
  const [erro, setErro] = useState(null)
  const [carregando, setCarregando] = useState(false)

  // faz o login via o gateway
  const fazerLogin = async (e) => {
    e.preventDefault()
    setErro(null)
    setCarregando(true)

    try {
      const response = await fetch('http://localhost:5000/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.erro || 'Falha ao autenticar no Keycloak')
      }

      setToken(data.access_token) 
    } catch (err) {
      setErro(err.message)
    } finally {
      setCarregando(false)
    }
  }

  // função para buscar os dados do Paciente
  const buscarPaciente = async () => {
    setErro(null)
    setDadosPaciente(null)
    setCarregando(true)

    try {
      const response = await fetch(`http://localhost:5000/api/pacientes/${pacienteId}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.erro || data.error || 'Acesso Negado')
      }

      setDadosPaciente(data)
    } catch (err) {
      setErro(err.message)
    } finally {
      setCarregando(false)
    }
  }

  const fazerLogout = () => {
    setToken(null)
    setDadosPaciente(null)
  }

  // --- TELA DE LOGIN ---
  if (!token) {
    return (
      <div style={{ padding: '40px', fontFamily: 'Arial, sans-serif', maxWidth: '400px', margin: '0 auto' }}>
        <h2>Login - Kiriland Hospital</h2>
        <form onSubmit={fazerLogin} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <input 
            type="text" 
            placeholder="Usuário (Ex: med.cardoso)" 
            value={username} 
            onChange={e => setUsername(e.target.value)} 
            style={{ padding: '10px' }}
          />
          <input 
            type="password" 
            placeholder="Senha" 
            value={password} 
            onChange={e => setPassword(e.target.value)} 
            style={{ padding: '10px' }}
          />
          <button type="submit" disabled={carregando} style={{ padding: '10px', backgroundColor: '#0056b3', color: 'white', border: 'none' }}>
            {carregando ? 'Autenticando...' : 'Entrar'}
          </button>
        </form>
        {erro && <p style={{ color: 'red', marginTop: '15px' }}>{erro}</p>}
      </div>
    )
  }

  // --- TELA DO SISTEMA ---
  return (
    <div style={{ padding: '40px', fontFamily: 'Arial, sans-serif', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <h1>Prontuário Eletrônico</h1>
        <button onClick={fazerLogout} style={{ padding: '8px', backgroundColor: '#dc3545', color: 'white', border: 'none', height: '35px' }}>Sair</button>
      </div>
      
      <div style={{ padding: '20px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
        <p><strong>Buscar Dados:</strong></p>
        <div style={{ display: 'flex', gap: '10px' }}>
          <input 
            type="text" 
            value={pacienteId}
            onChange={(e) => setPacienteId(e.target.value)}
            style={{ padding: '10px', flex: 1 }}
          />
          <button onClick={buscarPaciente} disabled={carregando} style={{ padding: '10px 20px', backgroundColor: '#28a745', color: 'white', border: 'none' }}>
            Buscar
          </button>
        </div>
      </div>

      {erro && <div style={{ padding: '15px', color: '#cc0000', backgroundColor: '#ffebee', marginTop: '20px' }}>{erro}</div>}

      {dadosPaciente && (
        <div style={{ padding: '20px', backgroundColor: '#e8f5e9', border: '1px solid #c8e6c9', borderRadius: '8px', marginTop: '20px' }}>
          <h2 style={{ marginTop: 0 }}>Resultado:</h2>
          <pre style={{ whiteSpace: 'pre-wrap', backgroundColor: '#fff', padding: '15px' }}>
            {JSON.stringify(dadosPaciente, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

export default App