import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './AdminDashboard.css';

const AdminGames = () => {
  const [games, setGames] = useState([]);
  const [projects, setProjects] = useState({});
  const [loading, setLoading] = useState(true);
  const [showCreateGame, setShowCreateGame] = useState(false);
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [selectedGame, setSelectedGame] = useState(null);

  const fetchGames = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/games`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setGames(response.data);
      response.data.forEach(game => {
        fetchProjects(game.id);
      });
    } catch (err) {
      console.error('获取游戏列表失败:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchProjects = async (gameId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/games/${gameId}/projects`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProjects(prev => ({ ...prev, [gameId]: response.data }));
    } catch (err) {
      console.error('获取项目列表失败:', err);
    }
  };

  useEffect(() => {
    fetchGames();
  }, [fetchGames]);

  const handleCreateGame = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const gameData = {
      name: formData.get('name'),
      description: formData.get('description'),
      icon: formData.get('icon')
    };

    try {
      const token = localStorage.getItem('token');
      await axios.post(`${import.meta.env.VITE_API_BASE_URL}/games`, gameData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      alert('游戏创建成功！');
      setShowCreateGame(false);
      fetchGames();
    } catch (err) {
      console.error('创建游戏失败:', err);
      alert('创建游戏失败！');
    }
  };

  const handleCreateProject = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const projectData = {
      name: formData.get('name'),
      description: formData.get('description'),
      price: parseFloat(formData.get('price')),
      unit: formData.get('unit'),
      icon: formData.get('icon')
    };

    try {
      const token = localStorage.getItem('token');
      await axios.post(`${import.meta.env.VITE_API_BASE_URL}/games/${selectedGame.id}/projects`, projectData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      alert('项目创建成功！');
      setShowCreateProject(false);
      fetchProjects(selectedGame.id);
    } catch (err) {
      console.error('创建项目失败:', err);
      alert('创建项目失败！');
    }
  };

  return (
    <div className="dashboard-container admin-dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>游戏管理</h1>
        </div>
        <div className="header-right">
          <button className="logout-btn" onClick={() => window.history.back()}>
            返回
          </button>
        </div>
      </header>
      
      <main className="dashboard-content">
        {loading ? (
          <div className="loading">加载中...</div>
        ) : (
          <div className="games-management">
            <div className="games-list">
              {games.map(game => (
                <div key={game.id} className="game-item">
                  <h3>{game.name}</h3>
                  <p>{game.description}</p>
                  <div className="projects-list">
                    {projects[game.id] && projects[game.id].map(project => (
                      <div key={project.id} className="project-item">
                        <span>{project.name}</span>
                        <span>¥{project.price}/{project.unit}</span>
                      </div>
                    ))}
                  </div>
                  <button 
                    className="card-btn"
                    onClick={() => {
                      setSelectedGame(game);
                      setShowCreateProject(true);
                    }}
                  >
                    添加项目
                  </button>
                </div>
              ))}
            </div>
            
            <button 
              className="create-btn"
              onClick={() => setShowCreateGame(true)}
            >
              添加游戏
            </button>
          </div>
        )}
      </main>

      {showCreateGame && (
        <div className="modal">
          <div className="modal-content">
            <h2>创建游戏</h2>
            <form onSubmit={handleCreateGame}>
              <input name="name" placeholder="游戏名称" required />
              <textarea name="description" placeholder="游戏描述" required />
              <input name="icon" placeholder="图标URL" />
              <div className="modal-buttons">
                <button type="submit">创建</button>
                <button type="button" onClick={() => setShowCreateGame(false)}>取消</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showCreateProject && selectedGame && (
        <div className="modal">
          <div className="modal-content">
            <h2>为 {selectedGame.name} 添加项目</h2>
            <form onSubmit={handleCreateProject}>
              <input name="name" placeholder="项目名称" required />
              <textarea name="description" placeholder="项目描述" required />
              <input name="price" type="number" placeholder="价格" step="0.01" required />
              <input name="unit" placeholder="单位（如：星、局）" required />
              <input name="icon" placeholder="图标URL" />
              <div className="modal-buttons">
                <button type="submit">创建</button>
                <button type="button" onClick={() => setShowCreateProject(false)}>取消</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminGames;
