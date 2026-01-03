import React, { useState } from 'react';
import './WorkflowDiagram.css';

const WorkflowDiagram = () => {
  const [selectedNode, setSelectedNode] = useState(null);

  const nodes = [
    {
      id: 'extract_intent',
      label: 'Extract Intent',
      description: 'LLM analyzes message to extract intent (single_car, fleet, policy_only) and slots (car_identifier, city, zone_phrase)',
      type: 'llm',
      position: { x: 50, y: 0 }
    },
    {
      id: 'resolve_car',
      label: 'Resolve Car',
      description: 'Matches car identifier to user\'s cars. Handles fleet or single car queries',
      type: 'logic',
      position: { x: 0, y: 100 }
    },
    {
      id: 'resolve_zone',
      label: 'Resolve Zone',
      description: 'Resolves city and zone phrase to specific pollution zones',
      type: 'service',
      position: { x: 100, y: 100 }
    },
    {
      id: 'fetch_policy',
      label: 'Fetch Policy',
      description: 'Retrieves pollution policy rules for the resolved zone',
      type: 'service',
      position: { x: 50, y: 200 }
    },
    {
      id: 'decide_eligibility',
      label: 'Decide Eligibility',
      description: 'Applies policy rules to car(s) to determine access eligibility',
      type: 'logic',
      position: { x: 50, y: 300 }
    },
    {
      id: 'format_reply',
      label: 'Format Reply',
      description: 'LLM generates natural language response based on decision',
      type: 'llm',
      position: { x: 50, y: 400 }
    }
  ];

  const edges = [
    { from: 'extract_intent', to: 'resolve_car', condition: 'single_car or fleet' },
    { from: 'extract_intent', to: 'resolve_zone', condition: 'policy_only' },
    { from: 'resolve_car', to: 'resolve_zone', condition: 'car resolved' },
    { from: 'resolve_zone', to: 'fetch_policy', condition: 'zone selected' },
    { from: 'fetch_policy', to: 'decide_eligibility', condition: 'has policy' },
    { from: 'decide_eligibility', to: 'format_reply', condition: 'decision made' }
  ];

  const stateFields = [
    { category: 'Input', fields: ['session_id', 'message', 'trace_id'] },
    { category: 'Intent Slots', fields: ['intent', 'car_identifier', 'city', 'zone_phrase'] },
    { category: 'Resolved Entities', fields: ['cars[]', 'selected_car', 'zone_candidates[]', 'selected_zone', 'policy'] },
    { category: 'Decisions', fields: ['decision', 'fleet_decisions[]'] },
    { category: 'Disambiguation', fields: ['pending_question', 'pending_type', 'disambiguation_options[]'] },
    { category: 'Output', fields: ['reply', 'next_step'] }
  ];

  return (
    <div className="workflow-diagram-container">
      <div className="diagram-header">
        <h2>🔄 LangGraph Workflow</h2>
        <p>Visual representation of the agent orchestration flow</p>
      </div>

      <div className="diagram-content">
        <div className="workflow-section">
          <h3>Execution Flow</h3>
          <div className="flow-diagram">
            {nodes.map((node) => (
              <div
                key={node.id}
                className={`flow-node ${node.type} ${selectedNode === node.id ? 'selected' : ''}`}
                style={{
                  top: `${node.position.y}px`,
                  left: `${node.position.x}%`
                }}
                onClick={() => setSelectedNode(selectedNode === node.id ? null : node.id)}
              >
                <div className="node-icon">
                  {node.type === 'llm' && '🤖'}
                  {node.type === 'service' && '🔧'}
                  {node.type === 'logic' && '⚙️'}
                </div>
                <div className="node-label">{node.label}</div>
                {selectedNode === node.id && (
                  <div className="node-tooltip">
                    {node.description}
                  </div>
                )}
              </div>
            ))}
            
            <svg className="flow-connections" viewBox="0 0 400 500">
              {edges.map((edge, idx) => {
                const fromNode = nodes.find(n => n.id === edge.from);
                const toNode = nodes.find(n => n.id === edge.to);
                const x1 = (fromNode.position.x / 100) * 400 + 80;
                const y1 = fromNode.position.y + 40;
                const x2 = (toNode.position.x / 100) * 400 + 80;
                const y2 = toNode.position.y + 10;
                
                return (
                  <g key={idx}>
                    <line
                      x1={x1}
                      y1={y1}
                      x2={x2}
                      y2={y2}
                      stroke="#4a90e2"
                      strokeWidth="2"
                      markerEnd="url(#arrowhead)"
                    />
                    {edge.condition && (
                      <text
                        x={(x1 + x2) / 2}
                        y={(y1 + y2) / 2}
                        fill="#666"
                        fontSize="10"
                        textAnchor="middle"
                      >
                        {edge.condition}
                      </text>
                    )}
                  </g>
                );
              })}
              <defs>
                <marker
                  id="arrowhead"
                  markerWidth="10"
                  markerHeight="10"
                  refX="9"
                  refY="3"
                  orient="auto"
                >
                  <polygon points="0 0, 10 3, 0 6" fill="#4a90e2" />
                </marker>
              </defs>
            </svg>
          </div>

          <div className="flow-legend">
            <div className="legend-item">
              <span className="legend-icon llm">🤖</span>
              <span>LLM Call</span>
            </div>
            <div className="legend-item">
              <span className="legend-icon service">🔧</span>
              <span>Service/API</span>
            </div>
            <div className="legend-item">
              <span className="legend-icon logic">⚙️</span>
              <span>Logic/Rules</span>
            </div>
          </div>
        </div>

        <div className="state-section">
          <h3>State Model (AgentState)</h3>
          <div className="state-groups">
            {stateFields.map((group, idx) => (
              <div key={idx} className="state-group">
                <h4>{group.category}</h4>
                <ul>
                  {group.fields.map((field, fIdx) => (
                    <li key={fIdx}>
                      <code>{field}</code>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="state-info">
            <p><strong>State Persistence:</strong> Session-based in-memory store</p>
            <p><strong>Updates:</strong> State flows through nodes, accumulating data</p>
            <p><strong>Disambiguation:</strong> State pauses at <code>pending_question=true</code></p>
          </div>
        </div>
      </div>

      <div className="diagram-footer">
        <div className="key-features">
          <h4>Key Features:</h4>
          <ul>
            <li><strong>Multi-turn conversations:</strong> State persists across turns</li>
            <li><strong>Smart disambiguation:</strong> Handles ambiguous queries with follow-up questions</li>
            <li><strong>Conditional routing:</strong> Different paths for single car, fleet, or policy queries</li>
            <li><strong>LLM integration:</strong> OpenAI for intent extraction and response formatting</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default WorkflowDiagram;
