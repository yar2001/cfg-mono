import { useCallback, useEffect, useMemo, useState } from 'react';
import { IoDownload, IoPlay } from 'react-icons/io5';
import { Subject } from 'rxjs';
import { createSourceFile, ScriptTarget, ScriptKind } from 'typescript';
import { CFGData, generateCFG, isCFGBlock } from '../../CFG';
import CodeEditor from '../../Editor';
import Mermaid from '../../Mermaid';
import { generateOutput } from '../../output';
import { evalInSandbox, variableToConsoleText } from '../../Sandbox';
import { defaultC, defaultCFGData, defaultJavaScript, defaultMermaid } from '../../template';
import { TemplateSelector } from '../../TemplateSelector';
import { ErrorBoundary } from '../../utils/errorBoundary';
import { Selector } from '../../Selector';
import axios from 'axios';

export function HomePage() {
  const [code, setCode] = useState(defaultJavaScript['foo']);

  const [editor$] = useState(new Subject<'format' | 'darkTheme' | 'dayTheme' | 'forceUpdateCode'>());

  const [consoleText, setConsoleText] = useState('');
  const onCodeChange = useCallback((code: string) => {
    setCode(code);
  }, []);

  const [lang, setLang] = useState('javascript');

  const [mermaidCode, setMermaidCode] = useState('');
  const [CSN, setCSN] = useState<Object>({});

  useEffect(() => {
    function drawCFG({ nodes, edges, lastNodes }: CFGData): string {
      let mermaidCode = '';
      nodes.forEach((node) => {
        node.text = node.text.replaceAll('"', "'");
        if (isCFGBlock(node)) {
          mermaidCode += `state "${node.text}" as ${node._id}{\n`;
          mermaidCode += drawCFG(node.children);
          mermaidCode += '\n}\n';
          return;
        }
        mermaidCode += `state "${node.text}" as ${node._id}\n`;
      });

      edges.forEach((edge) => {
        mermaidCode += `${edge.begin}-->${edge.end}\n`;
      });
      if (nodes.length) {
        mermaidCode += `[*]-->${nodes[0]._id}\n`;
      }
      lastNodes.forEach((node) => {
        mermaidCode += `${node._id}-->[*]\n`;
      });

      return mermaidCode;
    }

    switch (lang) {
      case 'javascript':
        const ast = createSourceFile('./src/index.ts', code, ScriptTarget.ES2016, true, ScriptKind.JS);

        const cfg = generateCFG(ast);
        const mermaid = 'stateDiagram-v2\n' + drawCFG(cfg);
        setMermaidCode(mermaid);
        break;
      case 'CFGData':
        try {
          setMermaidCode('stateDiagram-v2\n' + drawCFG(JSON.parse(code)));
        } catch (e) {
          console.error(e);
          setMermaidCode('stateDiagram-v2\n');
        }
        break;
      case 'mermaid':
        setMermaidCode(code);
        return;
      default:
        axios.post(`http://localhost:9000/${lang}/getCFG`, { code }).then(({ data }) => {
          setMermaidCode(data.mermaid);
          setCSN(data.CSN);
        });
    }
  }, [code, lang]);

  return (
    <>
      <div className="flex flex-col bg-gray-100 divide-y lg:grid grow lg:grid-rows-1 lg:grid-cols-2 lg:divide-x ">
        <div className="flex flex-col overflow-y-auto bg-white lg:h-screen">
          <div className="flex items-center justify-between gap-2 px-3 py-1">
            <div className="flex items-center gap-1">
              <Selector
                name="Language"
                value={lang}
                data={[
                  { title: 'JavaScript', key: 'javascript' },
                  { title: 'C', key: 'c' },
                  { title: 'Python', key: 'python' },
                  { title: 'CFGData', key: 'CFGData' },
                  { title: 'Mermaid', key: 'mermaid' },
                ]}
                onChange={(name) => {
                  setLang(name);
                  switch (name) {
                    case 'javascript':
                      setCode(defaultJavaScript['foo']);
                      break;
                    case 'c':
                      setCode(defaultC);
                      break;
                    case 'python':
                      setCode('print("Hello World")');
                      break;
                    case 'CFGData':
                      setCode(defaultCFGData);
                      break;
                    case 'mermaid':
                      setCode(defaultMermaid);
                      break;
                  }
                }}
                className="min-w-[192px] mb-1"
              />
              {lang === 'javascript' && (
                <TemplateSelector
                  onSelect={(name) => {
                    editor$.next('forceUpdateCode');
                    setCode(defaultJavaScript[name]);
                  }}
                />
              )}
            </div>
            <div className="flex items-center gap-2">
              <button
                className="flex items-center gap-2 px-3 py-1 transition-colors rounded-md bg-gray-50 active:bg-gray-100"
                onClick={() => {
                  const input = document.createElement('input');
                  input.type = 'file';
                  input.accept = '.jsonl,.json';
                  input.onchange = () => {
                    const file = input.files?.[0];
                    if (!file) return;
                    const reader = new FileReader();
                    reader.onload = async () => {
                      const text = reader.result as string;
                      const json = text
                        .split('\n')
                        .map((line) => {
                          try {
                            return JSON.parse(line);
                          } catch (e) {
                            console.log(line);
                            console.error(e);
                            return null;
                          }
                        })
                        .filter((x) => x !== null) as { code: string; text: string }[];
                      let output = [] as { CSN: any }[];
                      if (lang === 'javascript') {
                        output = json.map(({ code }) => ({ CSN: generateOutput(code) }));
                      } else {
                        const { data } = await axios.post(`http://localhost:9000/batch/${lang}`, { codes: json });
                        output = data;
                      }

                      const blob = new Blob(
                        output.map((x) => JSON.stringify(x) + '\n'),
                        { type: 'application/json' }
                      );

                      const a = document.createElement('a');
                      a.href = URL.createObjectURL(blob);
                      a.download = lang + '-output.jsonl';
                      a.click();
                    };
                    reader.readAsText(file);
                  };
                  input.click();
                }}
              >
                <IoDownload className="w-5 h-5 text-gray-500" />
                转换数据
              </button>

              {lang === 'javascript' && (
                <button
                  className="p-1 transition-colors rounded-md bg-blue-50 active:bg-blue-100"
                  onClick={() => {
                    console.log(generateOutput(code));
                    const GlobalEnv = {
                      Math,
                      Function,
                      Array,
                      Symbol,
                      Object,
                      Date,
                    };
                    setConsoleText((c) => c + '\n');
                    evalInSandbox(code, {
                      ...GlobalEnv,
                      console: {
                        log(...args: any[]) {
                          const consoleText = args.map((arg) => variableToConsoleText(arg)).join(' ');
                          setConsoleText((c) => c + consoleText + '\n');
                          console.log(...args);
                        },
                      },
                    });
                  }}
                >
                  <IoPlay className="w-5 h-5 text-blue-500" />
                </button>
              )}
            </div>
          </div>
          <CodeEditor
            language={lang === 'CFGData' ? 'json' : lang}
            noSemanticValidation
            value={code}
            onChange={onCodeChange}
            command$={editor$}
          />
          {lang === 'javascript' && (
            <div className="flex flex-col border-t">
              <div className="px-3 py-1 text-xs text-gray-800 select-none">Output</div>
              <div className="h-56 px-3 overflow-y-scroll">
                {consoleText.split('\n').map((text) => (
                  <p key={Math.random()}>{text}</p>
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="h-full overflow-y-auto bg-white lg:h-screen">
          <ErrorBoundary key={mermaidCode}>
            <Mermaid chart={mermaidCode} />
          </ErrorBoundary>
        </div>
      </div>
    </>
  );
}
