import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './AdminDashboard.css';

const DatabaseAdmin = () => {
  const navigate = useNavigate();
  const [tables, setTables] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTable, setActiveTable] = useState(null);
  const [tableData, setTableData] = useState([]);
  const [tableColumns, setTableColumns] = useState([]);
  const [dataLoading, setDataLoading] = useState(false);

  useEffect(() => {
    fetchTables();
  }, []);

  const fetchTables = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/admin/database/tables`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setTables(response.data);
    } catch (err) {
      console.error('获取表列表失败:', err);
      alert('获取表列表失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleTableClick = async (tableName) => {
    setActiveTable(tableName);
    setDataLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      
      // 获取表数据
      const dataResponse = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/admin/database/tables/${tableName}/data`,
        {
          headers: { Authorization: `Bearer ${token}` },
          params: {
            page: 1,
            page_size: 50
          }
        }
      );
      
      setTableData(dataResponse.data.data);
      setTableColumns(dataResponse.data.columns);
    } catch (err) {
      console.error('获取表数据失败:', err);
      alert('获取表数据失败: ' + (err.response?.data?.detail || err.message));
    } finally {
      setDataLoading(false);
    }
  };

  const handleBack = () => {
    setActiveTable(null);
    setTableData([]);
    setTableColumns([]);
  };

  const handleEditCell = (rowIndex, columnName, value) => {
    const newData = [...tableData];
    newData[rowIndex][columnName] = value;
    setTableData(newData);
  };

  const handleSaveRow = async (rowIndex) => {
    const row = tableData[rowIndex];
    const primaryKeyColumn = tableColumns.find(col => col.primary_key);
    
    if (!primaryKeyColumn) {
      alert('该表没有主键，无法更新数据');
      return;
    }
    
    const primaryKeyValue = row[primaryKeyColumn.name];
    
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${import.meta.env.VITE_API_BASE_URL}/admin/database/tables/${activeTable}/data/${primaryKeyValue}`,
        { data: row },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      alert('数据保存成功');
    } catch (err) {
      console.error('保存数据失败:', err);
      alert('保存数据失败: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDeleteRow = async (rowIndex) => {
    const row = tableData[rowIndex];
    const primaryKeyColumn = tableColumns.find(col => col.primary_key);
    
    if (!primaryKeyColumn) {
      alert('该表没有主键，无法删除数据');
      return;
    }
    
    const primaryKeyValue = row[primaryKeyColumn.name];
    
    if (!confirm(`确定要删除这条记录吗？\nID: ${primaryKeyValue}`)) {
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(
        `${import.meta.env.VITE_API_BASE_URL}/admin/database/tables/${activeTable}/data/${primaryKeyValue}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      // 从本地数据中移除
      const newData = [...tableData];
      newData.splice(rowIndex, 1);
      setTableData(newData);
      
      alert('数据删除成功');
    } catch (err) {
      console.error('删除数据失败:', err);
      alert('删除数据失败: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleAddRow = () => {
    const newRow = {};
    tableColumns.forEach(col => {
      newRow[col.name] = '';
    });
    setTableData([...tableData, newRow]);
  };

  const handleSaveNewRow = async (rowIndex) => {
    const newRow = tableData[rowIndex];
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/admin/database/tables/${activeTable}/data`,
        { data: newRow },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      alert('数据添加成功，ID: ' + response.data.id);
      // 刷新数据
      handleTableClick(activeTable);
    } catch (err) {
      console.error('添加数据失败:', err);
      alert('添加数据失败: ' + (err.response?.data?.detail || err.message));
    }
  };

  const formatValue = (value) => {
    if (value === null || value === undefined) {
      return 'NULL';
    }
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    return String(value);
  };

  return (
    <div className="dashboard-container admin-dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>{activeTable ? `数据库管理 - ${activeTable}` : '数据库管理'}</h1>
        </div>
        <div className="header-right">
          {activeTable ? (
            <button className="logout-btn" onClick={handleBack}>
              返回表列表
            </button>
          ) : (
            <button className="logout-btn" onClick={() => window.history.back()}>
              返回
            </button>
          )}
        </div>
      </header>
      
      <main className="dashboard-content">
        {loading ? (
          <div className="loading">加载中...</div>
        ) : !activeTable ? (
          // 表列表视图
          <div className="tables-list">
            <div className="table-stats">
              <p>共 {tables.length} 张表</p>
            </div>
            <div className="tables-grid">
              {tables.map(table => (
                <div key={table.name} className="table-card" onClick={() => handleTableClick(table.name)}>
                  <h3>{table.name}</h3>
                  <p>{table.comment || '无描述'}</p>
                  <div className="table-meta">
                    <span className="meta-item">列数: {table.columns.length}</span>
                    <span className="meta-item">行数: {table.row_count || 0}</span>
                  </div>
                  <button className="card-btn">查看数据</button>
                </div>
              ))}
            </div>
          </div>
        ) : (
          // 表数据视图
          <div className="table-data-view">
            <div className="data-actions">
              <button className="action-btn" onClick={handleAddRow}>添加新行</button>
              <button className="action-btn" onClick={() => handleTableClick(activeTable)}>刷新数据</button>
            </div>
            
            {dataLoading ? (
              <div className="loading">加载数据中...</div>
            ) : (
              <div className="data-table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      {tableColumns.map(col => (
                        <th key={col.name} title={`${col.type}${col.primary_key ? ' (主键)' : ''}`}>
                          {col.name}
                          {col.primary_key && <span className="pk-badge">PK</span>}
                        </th>
                      ))}
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tableData.map((row, rowIndex) => {
                      const isNewRow = !row.id && Object.values(row).every(val => val === '');
                      
                      return (
                        <tr key={rowIndex}>
                          {tableColumns.map(col => {
                            const value = row[col.name];
                            const isPrimaryKey = col.primary_key;
                            
                            return (
                              <td key={col.name}>
                                {isPrimaryKey && !isNewRow ? (
                                  <span className="pk-value">{formatValue(value)}</span>
                                ) : (
                                  <input
                                    type="text"
                                    value={value || ''}
                                    onChange={(e) => handleEditCell(rowIndex, col.name, e.target.value)}
                                    disabled={isPrimaryKey && !isNewRow}
                                    className="data-input"
                                  />
                                )}
                              </td>
                            );
                          })}
                          <td>
                            {isNewRow ? (
                              <button className="action-btn-small success" onClick={() => handleSaveNewRow(rowIndex)}>
                                保存
                              </button>
                            ) : (
                              <>
                                <button className="action-btn-small" onClick={() => handleSaveRow(rowIndex)}>
                                  保存
                                </button>
                                <button className="action-btn-small danger" onClick={() => handleDeleteRow(rowIndex)}>
                                  删除
                                </button>
                              </>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                
                {tableData.length === 0 && (
                  <div className="empty-data">表中暂无数据</div>
                )}
              </div>
            )}
            
            <div className="table-info">
              <h4>表结构信息</h4>
              <table className="schema-table">
                <thead>
                  <tr>
                    <th>列名</th>
                    <th>类型</th>
                    <th>可空</th>
                    <th>主键</th>
                    <th>默认值</th>
                  </tr>
                </thead>
                <tbody>
                  {tableColumns.map(col => (
                    <tr key={col.name}>
                      <td>{col.name}</td>
                      <td>{col.type}</td>
                      <td>{col.nullable ? '是' : '否'}</td>
                      <td>{col.primary_key ? '是' : '否'}</td>
                      <td>{col.default || 'NULL'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default DatabaseAdmin;