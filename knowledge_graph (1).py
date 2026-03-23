import spacy, networkx as nx, os, hashlib, json, html
from pyvis.network import Network
from collections import Counter
import re
import torch

APP_DIR = os.environ.get('APP_DIR', '.')

# Exact colors from your app.py Legend
COLOR_MAP = {
    'DOC': '#3b82f6',         
    'ORG': '#22c55e',         
    'PERSON': '#ec4899',      
    'LAW': '#f97316',         
    'GPE': '#eab308',         
    'LOC': '#eab308',         
    'EVENT': '#a855f7',       
    'PRODUCT': '#06b6d4',     
    'DEFAULT': '#94a3b8'      
}

def normalize_entity(text):
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text) 
    text = text.lower().replace("the ", "").strip()
    return text.title() 

def build_graph_from_documents(docs):
    G = nx.Graph()
    
    docs_by_file = {}
    for d in docs:
        fname = d['filename']
        if fname not in docs_by_file:
            docs_by_file[fname] = []
        docs_by_file[fname].append(d)
    
    docs_to_process = []
    # Grab chunks from up to 15 different PDFs
    for fname, chunks in list(docs_by_file.items())[:45]:
        docs_to_process.extend(chunks[:40])

    print(f"🧠 Booting up SpaCy Transformer to process {len(docs_to_process)} chunks...", flush=True)
    try:
        spacy.require_gpu()
        nlp = spacy.load("en_core_web_trf")
        print("✅ GPU Transformer Loaded Successfully!", flush=True)
    except Exception as e:
        print(f"❌ GPU Load Failed: {e}", flush=True)
        try:
            nlp = spacy.load("en_core_web_sm")
        except:
            return G 

    semantic_context = {}
    document_entities = {} 
    entity_labels = {} 

    allowed_labels = ['ORG', 'PERSON', 'GPE', 'LAW', 'EVENT', 'FAC', 'LOC', 'PRODUCT']

    for d in docs_to_process:
        text = d.get('content', '')[:30000] 
        doc = nlp(text)
        fname = d['filename']
        
        if fname not in document_entities:
            document_entities[fname] = [] # Use list so we can count frequencies per doc!

        for sent in doc.sents:
            for ent in sent.ents:
                if ent.label_ in allowed_labels and len(ent.text.strip()) > 2:
                    clean_name = normalize_entity(ent.text)
                    document_entities[fname].append(clean_name)
                    
                    if clean_name not in entity_labels:
                        entity_labels[clean_name] = ent.label_
                    
                    if clean_name not in semantic_context:
                        clean_sent = " ".join(sent.text.split())
                        semantic_context[clean_name] = clean_sent[:250] + "..."

    # --- FAIR DISTRIBUTION LOGIC ---
    for fname, entities_list in document_entities.items():
        source_node = f"Doc: {fname}"
        
        # Count entities JUST for this document, keep top 12
        doc_counter = Counter(entities_list)
        top_for_doc = [e for e, count in doc_counter.most_common(12)]
        
        if top_for_doc:
            G.add_node(source_node, label=f"📄 {fname[:20]}", color=COLOR_MAP['DOC'], size=30)
            
            for ent_name in top_for_doc:
                ctx = semantic_context.get(ent_name, "")
                
                # Safely escape quotes, THEN wrap in beautiful HTML
                safe_ent = html.escape(ent_name, quote=True)
                safe_ctx = html.escape(ctx, quote=True)
                tooltip = f'<div style="max-width:280px; white-space:normal; font-size:12px; color:#1e293b; padding:4px;"><b>{safe_ent}</b><hr style="margin:6px 0; border-color:#cbd5e1;"><i>{safe_ctx}</i></div>'
                
                if ent_name not in G:
                    label_type = entity_labels.get(ent_name, 'DEFAULT')
                    node_color = COLOR_MAP.get(label_type, COLOR_MAP['DEFAULT'])
                    G.add_node(ent_name, label=ent_name, title=tooltip, color=node_color)
                
                G.add_edge(source_node, ent_name)

    del nlp 
    if torch.cuda.is_available():
        torch.cuda.empty_cache() 
    print("✅ SpaCy unloaded. VRAM cleared!", flush=True)
    
    return G


def generate_interactive_graph(docs, force_rebuild=False):
    if not docs: return None

    output_path = os.path.join(APP_DIR, "graphs", "policy_kg.html")
    hash_path = os.path.join(APP_DIR, "graphs", "kg_hash.txt")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fingerprint_data = [{"file": d.get('filename'), "len": len(d.get('content', ''))} for d in docs]
    doc_fingerprint = hashlib.md5(json.dumps(fingerprint_data, sort_keys=True).encode()).hexdigest()

    force_rebuild = True 

    if not force_rebuild and os.path.exists(output_path) and os.path.exists(hash_path):
        try:
            with open(hash_path, 'r') as f:
                if f.read().strip() == doc_fingerprint: 
                    return output_path
        except: pass

    print("🔄 Building new Knowledge Graph (Cleaned & Pruned)...")
    G = build_graph_from_documents(docs)
    
    if len(G.nodes) == 0:
        return None  
   
    degrees = dict(G.degree())
    for node in G.nodes():
        degree_val = degrees.get(node, 1)
        G.nodes[node]['size'] = min(15 + (degree_val * 4), 55)
        G.nodes[node]['original_color'] = G.nodes[node].get('color', COLOR_MAP['DEFAULT'])

    net = Network(height="700px", width="100%", bgcolor="#0b0f19", font_color="white", notebook=False, cdn_resources="remote")
    net.from_nx(G)

    # --- REPULSION PHYSICS FOR WIDE GRAPH ---
    net.set_options("""
    var options = {
      "nodes": { "font": { "size": 13, "face": "Inter", "color": "#e2e8f0" }, "borderWidth": 0 },
      "edges": { "smooth": false, "color": { "color": "#334155", "highlight": "#818cf8" } },
      "physics": {
        "solver": "repulsion",
        "repulsion": { 
            "nodeDistance": 180,
            "centralGravity": 0.05,
            "springLength": 220,
            "springConstant": 0.05 
        },
        "stabilization": { "iterations": 150 }
      }
    }
    """)

    net.save_graph(output_path)

    with open(output_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    custom_js = """
    <script type="text/javascript">
        network.on("stabilizationIterationsDone", function () {
            network.setOptions( { physics: false } );
        });
        
        network.setOptions({ interaction: { selectConnectedEdges: false } });

        var currentSelectedNode = null;
        var currentHopDepth = 1;

        function getNodesWithinHops(startNodeId, maxHops) {
            var visited = new Set();
            var queue = [{id: startNodeId, depth: 0}];
            visited.add(startNodeId);
            
            while (queue.length > 0) {
                var current = queue.shift();
                if (current.depth < maxHops) {
                    var neighbors = network.getConnectedNodes(current.id);
                    for (var i = 0; i < neighbors.length; i++) {
                        if (!visited.has(neighbors[i])) { 
                            visited.add(neighbors[i]); 
                            queue.push({id: neighbors[i], depth: current.depth + 1}); 
                        }
                    }
                }
            }
            return Array.from(visited);
        }

        network.on("click", function (params) {
            var nodesDataset = network.body.data.nodes;
            var edgesDataset = network.body.data.edges;
            var allNodes = nodesDataset.get();
            var allEdges = edgesDataset.get();
            
            if (params.nodes.length > 0) {
                var clickedNodeId = params.nodes[0];
                
                if (clickedNodeId === currentSelectedNode) { 
                    currentHopDepth++; 
                } else { 
                    currentSelectedNode = clickedNodeId; 
                    currentHopDepth = 1; 
                }
                
                var activeNodes = getNodesWithinHops(clickedNodeId, currentHopDepth);
                
                for (var i = 0; i < allNodes.length; i++) {
                    var n = allNodes[i];
                    if (!n.original_color) n.original_color = n.color;
                    
                    if (activeNodes.includes(n.id)) {
                        n.color = n.original_color;
                        n.font = { color: '#ffffff', size: 16 };
                    } else {
                        n.color = 'rgba(100, 100, 100, 0.1)';
                        n.font = { color: 'rgba(100, 100, 100, 0.1)' };
                    }
                }
                nodesDataset.update(allNodes);

                for (var i = 0; i < allEdges.length; i++) {
                    var e = allEdges[i];
                    var fromActive = activeNodes.includes(e.from);
                    var toActive = activeNodes.includes(e.to);

                    if (fromActive && toActive) {
                        e.color = { color: '#818cf8', opacity: 1.0 };
                        e.width = 2;
                    } else {
                        e.color = { color: 'rgba(100, 100, 100, 0.05)', opacity: 0.05 };
                        e.width = 1;
                    }
                }
                edgesDataset.update(allEdges);

            } else {
                currentSelectedNode = null; 
                currentHopDepth = 1;
                
                for (var i = 0; i < allNodes.length; i++) {
                    var n = allNodes[i];
                    if (n.original_color) n.color = n.original_color;
                    n.font = { color: '#e2e8f0', size: 13 };
                }
                nodesDataset.update(allNodes);

                for (var i = 0; i < allEdges.length; i++) {
                    var e = allEdges[i];
                    e.color = { color: '#334155', opacity: 1.0 };
                    e.width = 1;
                }
                edgesDataset.update(allEdges);
            }
        });
    </script>
    """
    html_content = html_content.replace("</body>", custom_js + "\n</body>")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    with open(hash_path, 'w') as f:
        f.write(doc_fingerprint)

    return output_path