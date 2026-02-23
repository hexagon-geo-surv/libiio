find_program(SPHINX_EXECUTABLE NAMES sphinx-build)
if(SPHINX_EXECUTABLE)
    add_custom_target(sphinx
        COMMAND ${SPHINX_EXECUTABLE} -b html ${CMAKE_CURRENT_SOURCE_DIR} ${CMAKE_CURRENT_BINARY_DIR}/html
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        COMMENT "Generating Sphinx documentation"
    )
else()
    message(WARNING "Sphinx not found - cannot generate documentation")
endif()
