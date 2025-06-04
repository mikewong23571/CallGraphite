" CallGraphite - Neovim plugin for function call analysis

" 默认键盘映射
if !exists('g:callgraphite_disable_mappings')
    " 启动分析
    nnoremap <silent> <leader>cg :CallGraphite<CR>
    
    " 在调用栈中导航
    nnoremap <silent> <leader>cn :CallGraphiteNext<CR>
    nnoremap <silent> <leader>cp :CallGraphitePrev<CR>
    
    " 捕获当前函数
    nnoremap <silent> <leader>cc :CallGraphiteCapture<CR>
    
    " 生成可视化
    nnoremap <silent> <leader>cv :CallGraphiteVisualize<CR>
endif

" 命令别名
command! -nargs=0 CGStart :CallGraphite
command! -nargs=0 CGNext :CallGraphiteNext
command! -nargs=0 CGPrev :CallGraphitePrev
command! -nargs=0 CGCapture :CallGraphiteCapture
command! -nargs=0 CGVisualize :CallGraphiteVisualize

" Commands for setting up the plugin
command! CallGraphiteSetup echo "CallGraphite is ready to use!"