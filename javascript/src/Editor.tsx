import * as monaco from 'monaco-editor';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Subject } from 'rxjs';

export default function CodeEditor({
  value,
  onChange,
  command$,
  noSemanticValidation = false,
  extraLibs,
  language = 'javascript',
}: {
  value: string;
  onChange(code: string): void;
  command$?: Subject<'format' | 'darkTheme' | 'dayTheme' | 'forceUpdateCode'>;
  noSemanticValidation?: boolean;
  extraLibs?: {
    content: string;
    filePath?: string;
  }[];
  language?: string;
}) {
  const divRef = useRef<HTMLDivElement>(null);
  const [editor, setEditor] = useState<monaco.editor.IStandaloneCodeEditor>();

  const formatCode = useCallback(() => {
    if (!editor) return;
    editor.getAction('editor.action.formatDocument').run();
  }, [editor]);

  const setDarkMode = useCallback(
    (isDarkMode: boolean) => {
      if (!editor) return;
      monaco.editor.setTheme(isDarkMode ? 'vs-dark' : 'vs');
    },
    [editor]
  );

  const getCode = useCallback(() => {
    if (!editor) return;
    return editor.getValue();
  }, [editor]);

  const setCode = useCallback(
    (code: string) => {
      if (!editor) return;
      editor.setValue(code);
    },
    [editor]
  );

  useEffect(() => {
    if (!command$) return;

    const sub = command$.subscribe((command) => {
      switch (command) {
        case 'format':
          formatCode();
          break;
        case 'darkTheme':
          setDarkMode(true);
          break;
        case 'dayTheme':
          setDarkMode(false);
          break;
      }
    });
    return () => {
      sub.unsubscribe();
    };
  }, [command$, formatCode, setDarkMode]);

  useEffect(() => {
    if (getCode() === value) return;
    setCode(value);
  }, [getCode, setCode, value]);

  useEffect(() => {
    if (!divRef.current) return;
    let editor: monaco.editor.IStandaloneCodeEditor;
    monaco.languages.typescript.javascriptDefaults.setDiagnosticsOptions({
      noSuggestionDiagnostics: false,
      noSemanticValidation,
      noSyntaxValidation: false,
      diagnosticCodesToIgnore: [1108, 7044, 2451 /* redeclare */],
    });
    monaco.languages.typescript.javascriptDefaults.setCompilerOptions({
      target: monaco.languages.typescript.ScriptTarget.ESNext,
      allowNonTsExtensions: true,
      noImplicitAny: false,
    });
    monaco.languages.typescript.javascriptDefaults.setExtraLibs(extraLibs ?? []);
    monaco.editor.defineTheme('custom', {
      base: 'vs',
      inherit: true,
      rules: [{ token: 'invalid', foreground: '#000000' }],
      colors: {
        'editor.foreground': '#000000',
      },
    });
    editor = monaco.editor.create(divRef.current, {
      value: '',
      language,
      automaticLayout: true,
      minimap: {
        enabled: false,
      },
      unicodeHighlight: {
        ambiguousCharacters: false,
      },
      lineNumbersMinChars: 3,
      theme: 'custom',
    });

    setEditor(editor);
    return () => {
      editor.dispose();
    };
  }, [extraLibs, language, noSemanticValidation]);

  useEffect(() => {
    const model = editor?.getModel();
    if (!model) return;
    const sub = model.onDidChangeContent(() => {
      onChange?.(getCode() ?? '');
    });
    return () => {
      sub.dispose();
    };
  }, [editor, getCode, onChange]);

  return <div className="h-80 lg:h-full" ref={divRef}></div>;
}
